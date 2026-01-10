import logging
from typing import Optional
from data_ingestion.models.source_document import SourceDocument
from data_ingestion.selectors.source_document_selector import SourceDocumentSelector
from data_ingestion.repositories.source_document_repository import SourceDocumentRepository

logger = logging.getLogger('django')


class SourceDocumentService:
    """Service for SourceDocument business logic."""

    @staticmethod
    def get_all():
        """Get all source documents."""
        try:
            return SourceDocumentSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all source documents: {e}")
            return SourceDocumentSelector.get_none()

    @staticmethod
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
    def get_statistics():
        """Get source document statistics."""
        try:
            return SourceDocumentSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting source document statistics: {e}")
            return {}
