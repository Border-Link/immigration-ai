from .eligibility_result_service import EligibilityResultService
from .ai_reasoning_log_service import AIReasoningLogService
from .ai_citation_service import AICitationService
from .vector_db_service import PgVectorService
from .embedding_service import EmbeddingService
from .ai_reasoning_service import AIReasoningService
from .eligibility_check_service import EligibilityCheckService, EligibilityCheckResult

# Backward compatibility alias
VectorDBService = PgVectorService

__all__ = [
    'EligibilityResultService',
    'AIReasoningLogService',
    'AICitationService',
    'PgVectorService',
    'VectorDBService',  # Backward compatibility
    'EmbeddingService',
    'AIReasoningService',
    'EligibilityCheckService',
    'EligibilityCheckResult',
]

