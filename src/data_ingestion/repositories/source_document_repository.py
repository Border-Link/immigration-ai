from django.db import transaction, IntegrityError
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.models.source_document import SourceDocument
from data_ingestion.models.data_source import DataSource


class SourceDocumentRepository:
    """Repository for SourceDocument write operations."""

    @staticmethod
    def create_source_document(data_source: DataSource, source_url: str, raw_content: str,
                               content_type: str = 'text/html', http_status_code: int = None,
                               fetch_error: str = None):
        """Create a new source document."""
        with transaction.atomic():
            source_doc = SourceDocument.objects.create(
                data_source=data_source,
                source_url=source_url,
                raw_content=raw_content,
                content_type=content_type,
                http_status_code=http_status_code,
                fetch_error=fetch_error,
                version=1,
                is_deleted=False,
            )
            source_doc.full_clean()
            source_doc.save()
            return source_doc

    @staticmethod
    def soft_delete_source_document(source_document: SourceDocument, version: int = None) -> SourceDocument:
        """Soft delete a source document with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(source_document, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = SourceDocument.objects.filter(
                id=source_document.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = SourceDocument.objects.filter(id=source_document.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Source document not found.")
                raise ValidationError(
                    f"Source document was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return SourceDocument.objects.get(id=source_document.id)

    @staticmethod
    def delete_source_document(source_document: SourceDocument, version: int = None):
        """
        Delete a source document.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        SourceDocumentRepository.soft_delete_source_document(source_document, version=version)
        return True
