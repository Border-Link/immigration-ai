from django.db import transaction, IntegrityError
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.models.source_document import SourceDocument
from main_system.utils.file_hashing import ContentHash


class DocumentVersionRepository:
    """Repository for DocumentVersion write operations."""

    @staticmethod
    def create_document_version(source_document: SourceDocument, raw_text: str, 
                               metadata: dict = None):
        """Create a new document version."""
        with transaction.atomic():
            content_hash = ContentHash.compute_sha256(raw_text)
            
            # Check if version with same hash already exists
            existing = DocumentVersion.objects.filter(content_hash=content_hash).first()
            if existing:
                return existing

            try:
                version = DocumentVersion.objects.create(
                    source_document=source_document,
                    content_hash=content_hash,
                    raw_text=raw_text,
                    metadata=metadata or {},
                    version=1,
                    is_deleted=False,
                )
                version.full_clean()
                version.save()
                return version
            except IntegrityError:
                # Concurrency-safe: another worker may have created this content_hash concurrently.
                return DocumentVersion.objects.filter(content_hash=content_hash).first()

    @staticmethod
    def soft_delete_document_version(document_version: DocumentVersion, version: int = None) -> DocumentVersion:
        """Soft delete a document version with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(document_version, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated_count = DocumentVersion.objects.filter(
                id=document_version.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DocumentVersion.objects.filter(id=document_version.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Document version not found.")
                raise ValidationError(
                    f"Document version was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DocumentVersion.objects.get(id=document_version.id)

    @staticmethod
    def delete_document_version(document_version: DocumentVersion, version: int = None):
        """
        Delete a document version.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        DocumentVersionRepository.soft_delete_document_version(document_version, version=version)
        return True
