"""
Repository for ProcessingHistory write operations.
"""
from django.db import transaction
from document_processing.models.processing_history import ProcessingHistory
from document_handling.models.case_document import CaseDocument


class ProcessingHistoryRepository:
    """Repository for ProcessingHistory write operations."""

    @staticmethod
    def create_history_entry(
        case_document: CaseDocument,
        action: str,
        status: str,
        message: str = None,
        processing_job=None,
        user=None,
        metadata: dict = None,
        error_type: str = None,
        error_message: str = None,
        processing_time_ms: int = None
    ):
        """Create a new processing history entry."""
        with transaction.atomic():
            history = ProcessingHistory.objects.create(
                case_document=case_document,
                processing_job=processing_job,
                action=action,
                user=user,
                status=status,
                message=message,
                metadata=metadata,
                error_type=error_type,
                error_message=error_message,
                processing_time_ms=processing_time_ms
            )
            history.full_clean()
            history.save()
            return history

    @staticmethod
    def delete_history_entry(history):
        """Delete a processing history entry."""
        with transaction.atomic():
            history.delete()
            return True
