from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
from ai_decisions.models.ai_citation import AICitation
from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from data_ingestion.models.document_version import DocumentVersion


class AICitationRepository:
    """Repository for AICitation write operations."""

    @staticmethod
    def create_citation(reasoning_log: AIReasoningLog, document_version: DocumentVersion,
                       excerpt: str, relevance_score: float = None):
        """Create a new AI citation."""
        with transaction.atomic():
            citation = AICitation.objects.create(
                reasoning_log=reasoning_log,
                document_version=document_version,
                excerpt=excerpt,
                relevance_score=relevance_score
            )
            citation.full_clean()
            citation.save()
            return citation

    @staticmethod
    def update_citation(citation: AICitation, **fields):
        """Update citation fields."""
        return BaseRepositoryMixin.update_model_fields(
            citation,
            **fields,
            cache_keys=[f'ai_citation:{citation.id}']
        )

    @staticmethod
    def delete_citation(citation: AICitation):
        """Delete an AI citation."""
        with transaction.atomic():
            citation.delete()

