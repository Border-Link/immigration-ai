import pytest


@pytest.mark.django_db
class TestAiCallsOptimisticLocking:
    def test_call_summary_update_version_conflict_raises_validation_error(self, call_session_in_progress):
        from django.core.exceptions import ValidationError
        from ai_calls.repositories.call_summary_repository import CallSummaryRepository

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
        assert summary.version == 1

        # Wrong expected version should raise a conflict.
        with pytest.raises(ValidationError):
            CallSummaryRepository.update_call_summary(summary, version=999, attached_to_case=True)

    def test_call_transcript_update_version_conflict_raises_validation_error(self, call_session_in_progress):
        from django.core.exceptions import ValidationError
        from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository

        t = CallTranscriptRepository.create_transcript_turn(
            call_session=call_session_in_progress,
            turn_type="user",
            text="hello",
        )
        assert t.version == 1

        with pytest.raises(ValidationError):
            CallTranscriptRepository.update_transcript_turn(t, version=999, text="changed")

    def test_call_summary_soft_delete_filters_out_from_selector(self, call_session_in_progress):
        from ai_calls.repositories.call_summary_repository import CallSummaryRepository
        from ai_calls.selectors.call_summary_selector import CallSummarySelector

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
        assert CallSummarySelector.get_by_id(str(summary.id)) is not None

        CallSummaryRepository.delete_call_summary(summary, version=summary.version)
        assert CallSummarySelector.get_by_id(str(summary.id)) is None

