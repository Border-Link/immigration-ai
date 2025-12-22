from django.db import transaction
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
                fetch_error=fetch_error
            )
            source_doc.full_clean()
            source_doc.save()
            return source_doc

