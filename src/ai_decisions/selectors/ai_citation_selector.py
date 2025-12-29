from ai_decisions.models.ai_citation import AICitation
from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from data_ingestion.models.document_version import DocumentVersion


class AICitationSelector:
    """Selector for AICitation read operations."""

    @staticmethod
    def get_all():
        """Get all AI citations."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_reasoning_log(reasoning_log: AIReasoningLog):
        """Get citations by reasoning log."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).filter(reasoning_log=reasoning_log).order_by('-created_at')

    @staticmethod
    def get_by_document_version(document_version: DocumentVersion):
        """Get citations by document version."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).filter(document_version=document_version).order_by('-created_at')

    @staticmethod
    def get_by_id(citation_id):
        """Get citation by ID."""
        return AICitation.objects.select_related(
            'reasoning_log',
            'reasoning_log__case',
            'document_version',
            'document_version__source_document'
        ).get(id=citation_id)

