import logging
from typing import Optional
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.repositories.document_version_repository import DocumentVersionRepository
from data_ingestion.selectors.document_version_selector import DocumentVersionSelector

logger = logging.getLogger('django')


class DocumentVersionService:
    """Service for DocumentVersion business logic."""

    @staticmethod
    def get_all():
        """Get all document versions."""
        try:
            return DocumentVersionSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document versions: {e}")
            return DocumentVersion.objects.none()

    @staticmethod
    def get_by_source_document(source_document_id: str):
        """Get document versions by source document ID."""
        try:
            from data_ingestion.selectors.source_document_selector import SourceDocumentSelector
            source_document = SourceDocumentSelector.get_by_id(source_document_id)
            if not source_document:
                return DocumentVersion.objects.none()
            return DocumentVersionSelector.get_by_source_document(source_document)
        except Exception as e:
            logger.error(f"Error fetching document versions for source document {source_document_id}: {e}")
            return DocumentVersion.objects.none()

    @staticmethod
    def get_by_id(version_id: str) -> Optional[DocumentVersion]:
        """Get document version by ID."""
        try:
            return DocumentVersionSelector.get_by_id(version_id)
        except DocumentVersion.DoesNotExist:
            logger.error(f"Document version {version_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document version {version_id}: {e}")
            return None

    @staticmethod
    def get_latest_by_source_document(source_document_id: str) -> Optional[DocumentVersion]:
        """Get latest document version for a source document."""
        try:
            from data_ingestion.selectors.source_document_selector import SourceDocumentSelector
            source_document = SourceDocumentSelector.get_by_id(source_document_id)
            if not source_document:
                return None
            return DocumentVersionSelector.get_latest_by_source_document(source_document)
        except Exception as e:
            logger.error(f"Error fetching latest document version for source document {source_document_id}: {e}")
            return None

