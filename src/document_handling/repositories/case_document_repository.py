from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from main_system.repositories.base import BaseRepositoryMixin
from document_handling.models.case_document import CaseDocument
from immigration_cases.models.case import Case
from rules_knowledge.models.document_type import DocumentType


class CaseDocumentRepository:
    """Repository for CaseDocument write operations."""

    @staticmethod
    def create_case_document(case: Case, document_type: DocumentType, file_path: str,
                            file_name: str, file_size: int = None, mime_type: str = None,
                            status: str = 'uploaded'):
        """Create a new case document."""
        with transaction.atomic():
            case_document = CaseDocument.objects.create(
                case=case,
                document_type=document_type,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                status=status
            )
            case_document.full_clean()
            case_document.save()
            return case_document

    @staticmethod
    def update_case_document(case_document, version: int = None, **fields):
        """
        Update case document fields with optimistic locking.
        
        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(case_document, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in CaseDocument._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = timezone.now()

            updated_count = CaseDocument.objects.filter(
                id=case_document.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CaseDocument.objects.filter(id=case_document.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Case document not found.")
                raise ValidationError(
                    f"Case document was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CaseDocument.objects.get(id=case_document.id)

    @staticmethod
    def update_status(case_document, status: str, version: int = None):
        """Update document status with optimistic locking."""
        return CaseDocumentRepository.update_case_document(
            case_document,
            version=version,
            status=status
        )

    @staticmethod
    def soft_delete_case_document(case_document, version: int = None, deleted_by=None) -> CaseDocument:
        """
        Soft delete a case document with optimistic locking.
        
        Args:
            case_document: CaseDocument instance to soft delete
            version: Expected version number for optimistic locking
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted CaseDocument instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(case_document, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = CaseDocument.objects.filter(
                id=case_document.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CaseDocument.objects.filter(id=case_document.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Case document not found.")
                raise ValidationError(
                    f"Case document was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CaseDocument.objects.get(id=case_document.id)
    
    @staticmethod
    def delete_case_document(case_document, version: int = None, deleted_by=None):
        """
        Delete a case document (soft delete).
        
        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        CaseDocumentRepository.soft_delete_case_document(case_document, version=version, deleted_by=deleted_by)
        return True
    
    @staticmethod
    def restore_case_document(case_document, version: int = None, restored_by=None) -> CaseDocument:
        """
        Restore a soft-deleted case document with optimistic locking.
        
        Args:
            case_document: CaseDocument instance to restore
            version: Expected version number for optimistic locking
            restored_by: User performing the restoration
            
        Returns:
            Restored CaseDocument instance
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(case_document, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = CaseDocument.objects.filter(
                id=case_document.id,
                version=expected_version,
                is_deleted=True,
            ).update(
                is_deleted=False,
                deleted_at=None,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = CaseDocument.objects.filter(id=case_document.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Case document not found.")
                raise ValidationError(
                    f"Case document was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return CaseDocument.objects.get(id=case_document.id)

