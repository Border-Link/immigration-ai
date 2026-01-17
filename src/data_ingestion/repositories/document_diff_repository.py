from django.db import transaction, IntegrityError
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.models.document_diff import DocumentDiff
from data_ingestion.models.document_version import DocumentVersion


class DocumentDiffRepository:
    """Repository for DocumentDiff write operations."""

    @staticmethod
    def create_document_diff(old_version: DocumentVersion, new_version: DocumentVersion,
                            diff_text: str, change_type: str = 'minor_text'):
        """Create a new document diff."""
        with transaction.atomic():
            # Check if diff already exists
            existing = DocumentDiff.objects.filter(
                old_version=old_version,
                new_version=new_version
            ).first()
            if existing:
                return existing

            try:
                diff = DocumentDiff.objects.create(
                    old_version=old_version,
                    new_version=new_version,
                    diff_text=diff_text,
                    change_type=change_type,
                    version=1,
                    is_deleted=False,
                )
                diff.full_clean()
                diff.save()
                return diff
            except IntegrityError:
                # Concurrency-safe: another worker may have created this diff concurrently.
                return DocumentDiff.objects.filter(old_version=old_version, new_version=new_version).first()

    @staticmethod
    def soft_delete_document_diff(document_diff: DocumentDiff, version: int = None) -> DocumentDiff:
        """Soft delete a document diff with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(document_diff, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = DocumentDiff.objects.filter(
                id=document_diff.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentDiff.objects.filter(id=document_diff.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document diff not found.")
                raise ValidationError(
                    f"Document diff was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentDiff.objects.get(id=document_diff.id)

    @staticmethod
    def delete_document_diff(document_diff: DocumentDiff, version: int = None):
        """
        Delete a document diff.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        DocumentDiffRepository.soft_delete_document_diff(document_diff, version=version)
        return True
