import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result
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
    @cache_result(timeout=300, keys=[])  # 5 minutes - citations change when new reasoning occurs
    def get_all():
        """Get all AI citations."""
        try:
            return AICitationSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all AI citations: {e}")
            return AICitationSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['reasoning_log_id'])  # 5 minutes - cache citations by reasoning log
    def get_by_reasoning_log(reasoning_log_id: str):
        """Get citations by reasoning log."""
        try:
            reasoning_log = AIReasoningLogSelector.get_by_id(reasoning_log_id)
            return AICitationSelector.get_by_reasoning_log(reasoning_log)
        except Exception as e:
            logger.error(f"Error fetching citations for reasoning log {reasoning_log_id}: {e}")
            return AICitationSelector.get_none()
    
    @staticmethod
    @cache_result(timeout=300, keys=['document_version_id'])  # 5 minutes - cache citations by document version
    def get_by_document_version(document_version_id: str):
        """Get citations by document version."""
        try:
            document_version = DocumentVersionSelector.get_by_id(document_version_id)
            return AICitationSelector.get_by_document_version(document_version)
        except Exception as e:
            logger.error(f"Error fetching citations for document version {document_version_id}: {e}")
            return AICitationSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['citation_id'])  # 10 minutes - cache citation by ID
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

    @staticmethod
    def get_by_filters(reasoning_log_id: str = None, document_version_id: str = None, 
                       min_relevance: float = None, date_from=None, date_to=None):
        """Get AI citations with filters."""
        try:
            if reasoning_log_id:
                citations = AICitationService.get_by_reasoning_log(reasoning_log_id)
            elif document_version_id:
                citations = AICitationService.get_by_document_version(document_version_id)
            else:
                citations = AICitationSelector.get_all()
            
            # Apply additional filters
            if min_relevance is not None:
                citations = citations.filter(relevance_score__gte=min_relevance)
            if date_from:
                citations = citations.filter(created_at__gte=date_from)
            if date_to:
                citations = citations.filter(created_at__lte=date_to)
            
            return citations
        except Exception as e:
            logger.error(f"Error fetching filtered AI citations: {e}")
            return AICitationSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get AI citation statistics."""
        try:
            return AICitationSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting AI citation statistics: {e}")
            return {}
