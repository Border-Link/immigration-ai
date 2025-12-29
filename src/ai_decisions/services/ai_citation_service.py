import logging
from typing import Optional
from ai_decisions.models.ai_citation import AICitation
from ai_decisions.repositories.ai_citation_repository import AICitationRepository
from ai_decisions.selectors.ai_citation_selector import AICitationSelector
from ai_decisions.selectors.ai_reasoning_log_selector import AIReasoningLogSelector
from data_ingestion.selectors.document_version_selector import DocumentVersionSelector

logger = logging.getLogger('django')


class AICitationService:
    """Service for AICitation business logic."""

    @staticmethod
    def create_citation(reasoning_log_id: str, document_version_id: str, excerpt: str,
                       relevance_score: float = None) -> Optional[AICitation]:
        """Create a new AI citation."""
        try:
            reasoning_log = AIReasoningLogSelector.get_by_id(reasoning_log_id)
            document_version = DocumentVersionSelector.get_by_id(document_version_id)
            
            return AICitationRepository.create_citation(
                reasoning_log=reasoning_log,
                document_version=document_version,
                excerpt=excerpt,
                relevance_score=relevance_score
            )
        except Exception as e:
            logger.error(f"Error creating AI citation: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all AI citations."""
        try:
            return AICitationSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all AI citations: {e}")
            return AICitation.objects.none()

    @staticmethod
    def get_by_reasoning_log(reasoning_log_id: str):
        """Get citations by reasoning log."""
        try:
            reasoning_log = AIReasoningLogSelector.get_by_id(reasoning_log_id)
            return AICitationSelector.get_by_reasoning_log(reasoning_log)
        except Exception as e:
            logger.error(f"Error fetching citations for reasoning log {reasoning_log_id}: {e}")
            return AICitation.objects.none()

    @staticmethod
    def get_by_id(citation_id: str) -> Optional[AICitation]:
        """Get citation by ID."""
        try:
            return AICitationSelector.get_by_id(citation_id)
        except AICitation.DoesNotExist:
            logger.error(f"AI citation {citation_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching citation {citation_id}: {e}")
            return None

    @staticmethod
    def update_citation(citation_id: str, **fields) -> Optional[AICitation]:
        """Update citation fields."""
        try:
            citation = AICitationSelector.get_by_id(citation_id)
            return AICitationRepository.update_citation(citation, **fields)
        except AICitation.DoesNotExist:
            logger.error(f"AI citation {citation_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating citation {citation_id}: {e}")
            return None

    @staticmethod
    def delete_citation(citation_id: str) -> bool:
        """Delete an AI citation."""
        try:
            citation = AICitationSelector.get_by_id(citation_id)
            AICitationRepository.delete_citation(citation)
            return True
        except AICitation.DoesNotExist:
            logger.error(f"AI citation {citation_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting citation {citation_id}: {e}")
            return False

