from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from main_system.repositories.base import BaseRepositoryMixin
from document_handling.models.document_check import DocumentCheck
from document_handling.models.case_document import CaseDocument


class DocumentCheckRepository:
    """Repository for DocumentCheck write operations."""

    @staticmethod
    def create_document_check(case_document: CaseDocument, check_type: str, result: str,
                             details: dict = None, performed_by: str = None):
        """Create a new document check."""
        with transaction.atomic():
            document_check = DocumentCheck.objects.create(
                case_document=case_document,
                check_type=check_type,
                result=result,
                details=details,
                performed_by=performed_by
            )
            document_check.full_clean()
            document_check.save()
            return document_check

    @staticmethod
    def update_document_check(document_check, version: int = None, **fields):
        """
        Update document check fields with optimistic locking.
        
        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(document_check, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in DocumentCheck._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            updated_count = DocumentCheck.objects.filter(
                id=document_check.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentCheck.objects.filter(id=document_check.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document check not found.")
                raise ValidationError(
                    f"Document check was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentCheck.objects.get(id=document_check.id)

    @staticmethod
    def soft_delete_document_check(document_check, version: int = None, deleted_by=None) -> DocumentCheck:
        """
        Soft delete a document check with optimistic locking.
        
        Args:
            document_check: DocumentCheck instance to soft delete
            version: Expected version number for optimistic locking
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted DocumentCheck instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(document_check, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DocumentCheck.objects.filter(
                id=document_check.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentCheck.objects.filter(id=document_check.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document check not found.")
                raise ValidationError(
                    f"Document check was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentCheck.objects.get(id=document_check.id)
    
    @staticmethod
    def delete_document_check(document_check, version: int = None, deleted_by=None):
        """
        Delete a document check (soft delete).
        
        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        DocumentCheckRepository.soft_delete_document_check(document_check, version=version, deleted_by=deleted_by)
        return True
    
    @staticmethod
    def restore_document_check(document_check, version: int = None, restored_by=None) -> DocumentCheck:
        """
        Restore a soft-deleted document check with optimistic locking.
        
        Args:
            document_check: DocumentCheck instance to restore
            version: Expected version number for optimistic locking
            restored_by: User performing the restoration
            
        Returns:
            Restored DocumentCheck instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(document_check, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DocumentCheck.objects.filter(
                id=document_check.id,
                version=expected_version,
                is_deleted=True,
            ).update(
                is_deleted=False,
                deleted_at=None,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentCheck.objects.filter(id=document_check.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document check not found.")
                raise ValidationError(
                    f"Document check was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentCheck.objects.get(id=document_check.id)

