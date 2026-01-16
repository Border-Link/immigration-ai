"""
Tests for PostCallSummaryService.
"""

import pytest
from unittest.mock import MagicMock


@pytest.mark.django_db
class TestPostCallSummaryService:
    def test_generate_summary_returns_none_when_no_transcript(self, call_session_in_progress):
        from ai_calls.services.post_call_summary_service import PostCallSummaryService

        summary = PostCallSummaryService.generate_summary(str(call_session_in_progress.id))
        assert summary is None

    def test_generate_summary_success_with_mock_llm(self, monkeypatch, call_session_in_progress):
        from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository
        from ai_calls.services.post_call_summary_service import PostCallSummaryService

        # Create transcripts
        CallTranscriptRepository.create_transcript_turn(call_session=call_session_in_progress, turn_type="user", text="What docs do I need?", speech_confidence=0.9)
        CallTranscriptRepository.create_transcript_turn(call_session=call_session_in_progress, turn_type="ai", text="Based on your case information, you may need a passport.", ai_model="test-model")

        # Five LLM calls in generate_summary (key_questions, topics, action_items, next_steps, summary_text)
        llm_side_effects = [
            {"success": True, "content": '{"questions":["What docs do I need?"]}'},
            {"success": True, "content": '{"topics":["documents"]}'},
            {"success": True, "content": '{"action_items":["Upload passport"]}'},
            {"success": True, "content": '{"next_steps":["Upload passport"]}'},
            {"success": True, "content": "Here is your summary."},
        ]
        monkeypatch.setattr(
            PostCallSummaryService,
            "_call_llm_for_summary",
            MagicMock(side_effect=llm_side_effects),
        )

        summary = PostCallSummaryService.generate_summary(str(call_session_in_progress.id))
        assert summary is not None
        assert summary.summary_text
        assert summary.key_questions == ["What docs do I need?"]
        assert "documents" in summary.topics_discussed

    def test_generate_summary_invalid_json_falls_back(self, monkeypatch, call_session_in_progress):
        from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository
        from ai_calls.services.post_call_summary_service import PostCallSummaryService

        CallTranscriptRepository.create_transcript_turn(call_session=call_session_in_progress, turn_type="user", text="How long?", speech_confidence=0.9)
        CallTranscriptRepository.create_transcript_turn(call_session=call_session_in_progress, turn_type="ai", text="Based on your case information, timelines vary.", ai_model="test-model")

        monkeypatch.setattr(
            PostCallSummaryService,
            "_call_llm_for_summary",
            MagicMock(return_value={"success": True, "content": "not-json"}),
        )

        summary = PostCallSummaryService.generate_summary(str(call_session_in_progress.id))
        assert summary is not None
        assert isinstance(summary.key_questions, list)
        assert isinstance(summary.action_items, list)

    def test_attach_to_case_timeline_missing_entities_returns_false(self):
        from ai_calls.services.post_call_summary_service import PostCallSummaryService

        assert PostCallSummaryService.attach_to_case_timeline("00000000-0000-0000-0000-000000000000", "00000000-0000-0000-0000-000000000000") is False

    def test_attach_to_case_timeline_success_marks_attached(self, monkeypatch, call_session_in_progress, paid_case):
        from ai_calls.repositories.call_summary_repository import CallSummaryRepository
        from ai_calls.services.post_call_summary_service import PostCallSummaryService
        from ai_calls.selectors.call_summary_selector import CallSummarySelector

        case, _payment = paid_case
        summary = CallSummaryRepository.create_call_summary(
            call_session=call_session_in_progress,
            summary_text="Summary",
            total_turns=0,
            total_duration_seconds=0,
            key_questions=[],
            action_items=[],
            missing_documents=[],
            suggested_next_steps=[],
            topics_discussed=[],
        )
        assert summary is not None

        # Avoid coupling to immigration_cases status history details; assert we try to create it.
        from immigration_cases.repositories import case_status_history_repository as cshr_module
        monkeypatch.setattr(
            cshr_module.CaseStatusHistoryRepository,
            "create_status_history",
            MagicMock(name="create_status_history", return_value=True),
        )

        ok = PostCallSummaryService.attach_to_case_timeline(str(summary.id), str(case.id))
        assert ok is True

        updated = CallSummarySelector.get_by_id(str(summary.id))
        assert updated.attached_to_case is True

