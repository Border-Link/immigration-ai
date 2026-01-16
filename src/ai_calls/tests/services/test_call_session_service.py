"""
Tests for CallSessionService.

Focus:
- Normal lifecycle (create -> prepare -> start -> end)
- Retry logic
- Failure/edge cases and error handling
"""

import pytest
from unittest.mock import MagicMock
from django.utils import timezone


@pytest.mark.django_db
class TestCallSessionServiceCreate:
    def test_create_call_session_success(self, call_session_service, paid_case, case_owner):
        case, _payment = paid_case
        call_session = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert call_session is not None
        assert str(call_session.case_id) == str(case.id)
        assert str(call_session.user_id) == str(case_owner.id)
        assert call_session.status == "created"
        assert call_session.retry_count == 0

    def test_create_call_session_case_not_found_returns_none(self, call_session_service, case_owner):
        call_session = call_session_service.create_call_session(
            case_id="00000000-0000-0000-0000-000000000000",
            user_id=str(case_owner.id),
        )
        assert call_session is None

    def test_create_call_session_user_not_found_returns_none(self, call_session_service, paid_case):
        case, _payment = paid_case
        call_session = call_session_service.create_call_session(
            case_id=str(case.id),
            user_id="00000000-0000-0000-0000-000000000000",
        )
        assert call_session is None

    def test_create_call_session_case_not_owned_returns_none(self, call_session_service, paid_case, other_user):
        case, _payment = paid_case
        call_session = call_session_service.create_call_session(case_id=str(case.id), user_id=str(other_user.id))
        assert call_session is None

    def test_create_call_session_case_closed_returns_none(self, call_session_service, case_service, paid_case, case_owner):
        case, _payment = paid_case
        updated, err, _status = case_service.update_case(
            case_id=str(case.id),
            updated_by_id=str(case_owner.id),
            reason="close for ai calls test",
            version=case.version,
            status="closed",
        )
        assert err is None
        assert updated is not None

        call_session = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert call_session is None

    def test_create_call_session_active_call_exists_returns_none(self, call_session_service, paid_case, case_owner):
        case, _payment = paid_case
        first = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert first is not None
        second = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert second is None

    def test_create_call_session_retry_success_for_abrupt_end(self, call_session_service, paid_case, case_owner, monkeypatch):
        """
        Retry allowed only if parent session ended abruptly (terminated/failed/expired)
        within 10 minutes.
        """
        case, _payment = paid_case
        parent = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert parent is not None

        # Mark parent as terminated quickly (abrupt end)
        from ai_calls.repositories.call_session_repository import CallSessionRepository

        parent = CallSessionRepository.update_call_session(
            parent,
            version=parent.version,
            status="terminated",
            started_at=timezone.now(),
            ended_at=timezone.now(),
            duration_seconds=120,
        )

        retry = call_session_service.create_call_session(
            case_id=str(case.id),
            user_id=str(case_owner.id),
            parent_session_id=str(parent.id),
        )
        assert retry is not None
        assert retry.parent_session_id == parent.id
        assert retry.retry_count == parent.retry_count + 1

    def test_create_call_session_retry_rejects_non_abrupt_parent(self, call_session_service, paid_case, case_owner):
        case, _payment = paid_case
        parent = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert parent is not None

        retry = call_session_service.create_call_session(
            case_id=str(case.id),
            user_id=str(case_owner.id),
            parent_session_id=str(parent.id),
        )
        assert retry is None

    def test_create_call_session_retry_rejects_long_duration(self, call_session_service, paid_case, case_owner):
        case, _payment = paid_case
        parent = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
        assert parent is not None

        from ai_calls.repositories.call_session_repository import CallSessionRepository

        parent = CallSessionRepository.update_call_session(
            parent,
            version=parent.version,
            status="terminated",
            duration_seconds=601,
        )

        retry = call_session_service.create_call_session(
            case_id=str(case.id),
            user_id=str(case_owner.id),
            parent_session_id=str(parent.id),
        )
        assert retry is None


@pytest.mark.django_db
class TestCallSessionServiceLifecycle:
    def test_prepare_call_session_success(self, call_session_ready):
        assert call_session_ready.status == "ready"
        assert call_session_ready.context_bundle is not None
        assert call_session_ready.context_hash is not None
        assert call_session_ready.ready_at is not None

    def test_prepare_call_session_wrong_state_returns_none(self, call_session_service, call_session_ready):
        again = call_session_service.prepare_call_session(str(call_session_ready.id))
        assert again is None

    def test_prepare_call_session_context_build_failure_marks_failed(self, call_session_service, call_session_created, monkeypatch):
        from ai_calls.services import case_context_builder as case_context_builder_module
        from ai_calls.selectors.call_session_selector import CallSessionSelector

        monkeypatch.setattr(
            case_context_builder_module.CaseContextBuilder,
            "build_context_bundle",
            MagicMock(name="build_context_bundle", return_value={}),
        )

        result = call_session_service.prepare_call_session(str(call_session_created.id))
        assert result is None

        # Session should be marked failed (best-effort)
        updated = CallSessionSelector.get_by_id(str(call_session_created.id))
        assert updated.status == "failed"

    def test_start_call_success(self, call_session_in_progress):
        assert call_session_in_progress.status == "in_progress"
        assert call_session_in_progress.started_at is not None
        assert call_session_in_progress.timebox_task_id is not None

    def test_start_call_without_context_marks_failed(self, call_session_service, call_session_created):
        # Put session into ready without a context_bundle (invalid)
        from ai_calls.repositories.call_session_repository import CallSessionRepository
        from ai_calls.selectors.call_session_selector import CallSessionSelector

        call_session = CallSessionRepository.update_call_session(
            call_session_created,
            version=call_session_created.version,
            status="ready",
            context_bundle=None,
        )
        assert call_session.status == "ready"
        result = call_session_service.start_call(str(call_session.id))
        assert result is None

        updated = CallSessionSelector.get_by_id(str(call_session.id))
        assert updated.status == "failed"

    def test_end_call_success_without_summary_when_no_transcripts(self, call_session_service, call_session_in_progress, monkeypatch):
        from ai_calls.services import post_call_summary_service as summary_module
        from ai_calls.services import timebox_service as timebox_service_module

        monkeypatch.setattr(
            timebox_service_module.TimeboxService,
            "cancel_timebox_enforcement",
            MagicMock(name="cancel_timebox_enforcement", return_value=True),
        )
        monkeypatch.setattr(
            summary_module.PostCallSummaryService,
            "generate_summary",
            MagicMock(name="generate_summary", return_value=None),
        )
        monkeypatch.setattr(
            summary_module.PostCallSummaryService,
            "attach_to_case_timeline",
            MagicMock(name="attach_to_case_timeline", return_value=True),
        )

        ended = call_session_service.end_call(str(call_session_in_progress.id))
        assert ended is not None
        assert ended.status == "completed"
        assert ended.ended_at is not None
        assert ended.duration_seconds is not None
        assert ended.timebox_task_id is None
        assert ended.summary is None

    def test_end_call_attaches_summary_when_generated(self, call_session_service, call_session_in_progress, monkeypatch):
        from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository
        from ai_calls.repositories.call_summary_repository import CallSummaryRepository
        from ai_calls.services import post_call_summary_service as summary_module
        from ai_calls.services import timebox_service as timebox_service_module

        # Create minimal transcripts via repository (no direct model usage in tests)
        CallTranscriptRepository.create_transcript_turn(call_session=call_session_in_progress, turn_type="user", text="Hello?", speech_confidence=0.9)
        CallTranscriptRepository.create_transcript_turn(call_session=call_session_in_progress, turn_type="ai", text="Based on your case information, here is some guidance.", ai_model="test-model")

        def _fake_generate(session_id: str):
            return CallSummaryRepository.create_call_summary(
                call_session=call_session_in_progress,
                summary_text="Summary",
                total_turns=2,
                total_duration_seconds=10,
                key_questions=["Hello?"],
                action_items=[],
                missing_documents=[],
                suggested_next_steps=[],
                topics_discussed=["general_information"],
            )

        monkeypatch.setattr(
            timebox_service_module.TimeboxService,
            "cancel_timebox_enforcement",
            MagicMock(name="cancel_timebox_enforcement", return_value=True),
        )
        monkeypatch.setattr(summary_module.PostCallSummaryService, "generate_summary", MagicMock(name="generate_summary", side_effect=_fake_generate))
        monkeypatch.setattr(summary_module.PostCallSummaryService, "attach_to_case_timeline", MagicMock(name="attach_to_case_timeline", return_value=True))

        ended = call_session_service.end_call(str(call_session_in_progress.id))
        assert ended is not None
        assert ended.status == "completed"
        assert ended.summary is not None

    def test_terminate_call_success(self, call_session_service, call_session_in_progress, case_owner, monkeypatch):
        from ai_calls.services import timebox_service as timebox_service_module
        monkeypatch.setattr(
            timebox_service_module.TimeboxService,
            "cancel_timebox_enforcement",
            MagicMock(name="cancel_timebox_enforcement", return_value=True),
        )

        terminated = call_session_service.terminate_call(
            session_id=str(call_session_in_progress.id),
            reason="user requested",
            terminated_by_user_id=str(case_owner.id),
        )
        assert terminated is not None
        assert terminated.status == "terminated"
        assert terminated.ended_at is not None

    def test_fail_call_session_non_terminal(self, call_session_service, call_session_in_progress, monkeypatch):
        from ai_calls.services import timebox_service as timebox_service_module
        monkeypatch.setattr(
            timebox_service_module.TimeboxService,
            "cancel_timebox_enforcement",
            MagicMock(name="cancel_timebox_enforcement", return_value=True),
        )

        failed = call_session_service.fail_call_session(
            session_id=str(call_session_in_progress.id),
            reason="system error",
            error_details={"x": 1},
        )
        assert failed is not None
        assert failed.status == "failed"

    def test_update_heartbeat_skips_when_not_in_progress(self, call_session_service, call_session_ready):
        # Not in progress: should return session unchanged
        res = call_session_service.update_heartbeat(str(call_session_ready.id))
        assert res is not None
        assert res.status == "ready"

    def test_update_heartbeat_updates_when_in_progress(self, call_session_service, call_session_in_progress):
        # In progress: should update and return session
        res2 = call_session_service.update_heartbeat(str(call_session_in_progress.id))
        assert res2 is not None
        assert res2.status == "in_progress"

