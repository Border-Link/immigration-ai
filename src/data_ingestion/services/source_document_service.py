import logging
from typing import Optional
from data_ingestion.models.source_document import SourceDocument
from data_ingestion.selectors.source_document_selector import SourceDocumentSelector

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
            return SourceDocument.objects.none()

    @staticmethod
    def get_by_data_source(data_source_id: str):
        """Get source documents by data source ID."""
        try:
            from data_ingestion.selectors.data_source_selector import DataSourceSelector
            data_source = DataSourceSelector.get_by_id(data_source_id)
            if not data_source:
                return SourceDocument.objects.none()
            return SourceDocumentSelector.get_by_data_source(data_source)
        except Exception as e:
            logger.error(f"Error fetching source documents for data source {data_source_id}: {e}")
            return SourceDocument.objects.none()

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

