from django.db import transaction
from ai_calls.models.call_summary import CallSummary


class CallSummaryRepository:
    """Repository for CallSummary write operations."""

    @staticmethod
    def create_call_summary(call_session, summary_text: str, total_turns: int, total_duration_seconds: int, **fields):
        """Create a new call summary."""
        with transaction.atomic():
            summary = CallSummary.objects.create(
                call_session=call_session,
                summary_text=summary_text,
                total_turns=total_turns,
                total_duration_seconds=total_duration_seconds,
                **fields
            )
            summary.full_clean()
            summary.save()
            return summary

    @staticmethod
    def update_call_summary(summary: CallSummary, **fields):
        """Update call summary fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(summary, key):
                    setattr(summary, key, value)
            
            summary.full_clean()
            summary.save()
            return summary

    @staticmethod
    def delete_call_summary(summary: CallSummary):
        """Delete a call summary."""
        with transaction.atomic():
            summary.delete()
