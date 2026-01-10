"""
AI Citation Read-Only API Views

Read-only endpoints for viewing AI citations.
Used for debugging, auditing, and citation quality analysis.
Access restricted to reviewers (who review AI decisions) and staff/superusers.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_reviewer import IsReviewer
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.serializers.ai_citation.read import AICitationSerializer, AICitationListSerializer

logger = logging.getLogger('django')


class AICitationListAPI(AuthAPI):
    """
    Get list of AI citations.
    
    Endpoint: GET /api/v1/ai-decisions/ai-citations/
    Auth: Required (reviewer only - reviewers review AI decisions)
    Query Params:
        - reasoning_log_id: Filter by reasoning log ID
        - document_version_id: Filter by document version ID
    """
    permission_classes = [IsReviewer]
    
    def get(self, request):
        reasoning_log_id = request.query_params.get('reasoning_log_id', None)
        document_version_id = request.query_params.get('document_version_id', None)
        
        try:
            if reasoning_log_id:
                citations = AICitationService.get_by_reasoning_log(reasoning_log_id)
            elif document_version_id:
                citations = AICitationService.get_by_document_version(document_version_id)
            else:
                citations = AICitationService.get_all()
            
            return self.api_response(
                message="AI citations retrieved successfully.",
                data=AICitationListSerializer(citations, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving AI citations: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving AI citations.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AICitationDetailAPI(AuthAPI):
    """
    Get AI citation by ID.
    
    Endpoint: GET /api/v1/ai-decisions/ai-citations/<id>/
    Auth: Required (reviewer only - reviewers review AI decisions)
    """
    permission_classes = [IsReviewer]
    
    def get(self, request, id):
        try:
            citation = AICitationService.get_by_id(id)
            if not citation:
                return self.api_response(
                    message=f"AI citation with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="AI citation retrieved successfully.",
                data=AICitationSerializer(citation).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving AI citation {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving AI citation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
