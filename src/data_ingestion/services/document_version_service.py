import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
from data_ingestion.repositories.document_version_repository import DocumentVersionRepository

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "document_versions"


class DocumentVersionService:
    """Service for DocumentVersion business logic."""

    @staticmethod
    @cache_result(timeout=600, keys=[], namespace=namespace, user_scope="global")  # 10 minutes - document versions change when ingested
    def get_all():
        """Get all document versions."""
        try:
            return DocumentVersionSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document versions: {e}")
            return DocumentVersionSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['source_document_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache versions by source document
    def get_by_source_document(source_document_id: str):
        """Get document versions by source document ID."""
        try:
            from data_ingestion.selectors.source_document_selector import SourceDocumentSelector
            source_document = SourceDocumentSelector.get_by_id(source_document_id)
            if not source_document:
                return DocumentVersionSelector.get_none()
            return DocumentVersionSelector.get_by_source_document(source_document)
        except Exception as e:
            logger.error(f"Error fetching document versions for source document {source_document_id}: {e}")
            return DocumentVersionSelector.get_none()

    @staticmethod
    @cache_result(timeout=3600, keys=['version_id'], namespace=namespace, user_scope="global")  # 1 hour - cache version by ID
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
    @cache_result(timeout=1800, keys=['source_document_id'], namespace=namespace, user_scope="global")  # 30 minutes - latest version changes when new version ingested
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

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_document_version(version_id: str) -> bool:
        """Delete a document version."""
        try:
            version = DocumentVersionSelector.get_by_id(version_id)
            if not version:
                logger.error(f"Document version {version_id} not found")
                return False
            DocumentVersionRepository.delete_document_version(version)
            return True
        except DocumentVersion.DoesNotExist:
            logger.error(f"Document version {version_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document version {version_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(source_document_id: str = None, date_from=None, date_to=None):
        """Get document versions with filters."""
        try:
            from data_ingestion.selectors.source_document_selector import SourceDocumentSelector
            
            source_document = None
            if source_document_id:
                source_document = SourceDocumentSelector.get_by_id(source_document_id)
            
            return DocumentVersionSelector.get_by_filters(
                source_document=source_document,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error fetching filtered document versions: {e}")
            return DocumentVersionSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get document version statistics."""
        try:
            return DocumentVersionSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting document version statistics: {e}")
            return {}
