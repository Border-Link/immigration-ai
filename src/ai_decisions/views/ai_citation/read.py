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
from ai_decisions.serializers.ai_citation.read import (
    AICitationListQuerySerializer,
    AICitationSerializer,
    AICitationListSerializer
)
from main_system.utils import paginate_queryset

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
        # Validate query parameters
        query_serializer = AICitationListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        reasoning_log_id = validated_params.get('reasoning_log_id')
        document_version_id = validated_params.get('document_version_id')
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        
        if reasoning_log_id:
            citations = AICitationService.get_by_reasoning_log(str(reasoning_log_id))
        elif document_version_id:
            citations = AICitationService.get_by_document_version(str(document_version_id))
        else:
            citations = AICitationService.get_all()
        
        # Paginate results
        paginated_citations, pagination_metadata = paginate_queryset(citations, page=page, page_size=page_size)
        
        return self.api_response(
            message="AI citations retrieved successfully.",
            data={
                'items': AICitationListSerializer(paginated_citations, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class AICitationDetailAPI(AuthAPI):
    """
    Get AI citation by ID.
    
    Endpoint: GET /api/v1/ai-decisions/ai-citations/<id>/
    Auth: Required (reviewer only - reviewers review AI decisions)
    """
    permission_classes = [IsReviewer]
    
    def get(self, request, id):
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
