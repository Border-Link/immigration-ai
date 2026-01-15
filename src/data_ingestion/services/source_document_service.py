import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from data_ingestion.models.source_document import SourceDocument
from data_ingestion.selectors.source_document_selector import SourceDocumentSelector
from data_ingestion.repositories.source_document_repository import SourceDocumentRepository

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "source_documents"


class SourceDocumentService:
    """Service for SourceDocument business logic."""

    @staticmethod
    @cache_result(timeout=600, keys=[], namespace=namespace, user_scope="global")  # 10 minutes - documents change when ingested
    def get_all():
        """Get all source documents."""
        try:
            return SourceDocumentSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all source documents: {e}")
            return SourceDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['data_source_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache documents by data source
    def get_by_data_source(data_source_id: str):
        """Get source documents by data source ID."""
        try:
            from data_ingestion.selectors.data_source_selector import DataSourceSelector
            data_source = DataSourceSelector.get_by_id(data_source_id)
            if not data_source:
                return SourceDocumentSelector.get_none()
            return SourceDocumentSelector.get_by_data_source(data_source)
        except Exception as e:
            logger.error(f"Error fetching source documents for data source {data_source_id}: {e}")
            return SourceDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=3600, keys=['document_id'], namespace=namespace, user_scope="global")  # 1 hour - cache document by ID
    def get_by_id(document_id: str) -> Optional[SourceDocument]:
        """Get source document by ID."""
        try:
            return SourceDocumentSelector.get_by_id(document_id)
        except SourceDocument.DoesNotExist:
            logger.error(f"Source document {document_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching source document {document_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=1800, keys=['data_source_id'], namespace=namespace, user_scope="global")  # 30 minutes - latest document changes when new one ingested
    def get_latest_by_data_source(data_source_id: str) -> Optional[SourceDocument]:
        """Get latest source document for a data source."""
        try:
            from data_ingestion.selectors.data_source_selector import DataSourceSelector
            data_source = DataSourceSelector.get_by_id(data_source_id)
            if not data_source:
                return None
            return SourceDocumentSelector.get_latest_by_data_source(data_source)
        except Exception as e:
            logger.error(f"Error fetching latest source document for data source {data_source_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_source_document(document_id: str) -> bool:
        """Delete a source document."""
        try:
            document = SourceDocumentSelector.get_by_id(document_id)
            if not document:
                logger.error(f"Source document {document_id} not found")
                return False
            SourceDocumentRepository.delete_source_document(document)
            return True
        except SourceDocument.DoesNotExist:
            logger.error(f"Source document {document_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting source document {document_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(data_source_id: str = None, has_error: bool = None, http_status: int = None, date_from=None, date_to=None):
        """Get source documents with filters."""
        try:
            from data_ingestion.selectors.data_source_selector import DataSourceSelector
            
            data_source = None
            if data_source_id:
                data_source = DataSourceSelector.get_by_id(data_source_id)
            
            return SourceDocumentSelector.get_by_filters(
                data_source=data_source,
                has_error=has_error,
                http_status=http_status,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error fetching filtered source documents: {e}")
            return SourceDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get source document statistics."""
        try:
            return SourceDocumentSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting source document statistics: {e}")
            return {}
