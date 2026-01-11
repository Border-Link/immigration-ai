from django.db import transaction
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
            
            version = DocumentVersion.objects.create(
                source_document=source_document,
                content_hash=content_hash,
                raw_text=raw_text,
                metadata=metadata or {}
            )
            version.full_clean()
            version.save()
            return version

    @staticmethod
    def delete_document_version(document_version):
        """Delete a document version."""
        with transaction.atomic():
            document_version.delete()
            return True
