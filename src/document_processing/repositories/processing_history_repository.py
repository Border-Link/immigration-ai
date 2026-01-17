"""
Repository for ProcessingHistory write operations.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
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
    def soft_delete_history_entry(history, version: int = None, deleted_by=None) -> ProcessingHistory:
        """
        Soft delete a processing history entry with optimistic locking.
        
        Args:
            history: ProcessingHistory instance to soft delete
            version: Expected version number for optimistic locking
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted ProcessingHistory instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(history, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ProcessingHistory.objects.filter(
                id=history.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ProcessingHistory.objects.filter(id=history.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Processing history entry not found.")
                raise ValidationError(
                    f"Processing history entry was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ProcessingHistory.objects.get(id=history.id)
    
    @staticmethod
    def delete_history_entry(history, version: int = None, deleted_by=None):
        """
        Delete a processing history entry (soft delete).
        
        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        ProcessingHistoryRepository.soft_delete_history_entry(history, version=version, deleted_by=deleted_by)
        return True
    
    @staticmethod
    def restore_history_entry(history, version: int = None, restored_by=None) -> ProcessingHistory:
        """
        Restore a soft-deleted processing history entry with optimistic locking.
        
        Args:
            history: ProcessingHistory instance to restore
            version: Expected version number for optimistic locking
            restored_by: User performing the restoration
            
        Returns:
            Restored ProcessingHistory instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(history, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = ProcessingHistory.objects.filter(
                id=history.id,
                version=expected_version,
                is_deleted=True,
            ).update(
                is_deleted=False,
                deleted_at=None,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = ProcessingHistory.objects.filter(id=history.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Processing history entry not found.")
                raise ValidationError(
                    f"Processing history entry was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return ProcessingHistory.objects.get(id=history.id)
