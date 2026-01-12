"""
Admin API Views for AICitation Management

Admin-only endpoints for managing AI citations.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.serializers.ai_citation.read import AICitationSerializer, AICitationListSerializer
from ai_decisions.serializers.ai_citation.admin import AICitationAdminListQuerySerializer
from main_system.utils import paginate_queryset

logger = logging.getLogger('django')


class AICitationAdminListAPI(AuthAPI):
    """
    Admin: Get list of all AI citations with advanced filtering.
    
    Endpoint: GET /api/v1/ai-decisions/admin/ai-citations/
    Auth: Required (staff/superuser only)
    Query Params:
        - reasoning_log_id: Filter by reasoning log ID
        - document_version_id: Filter by document version ID
        - min_relevance: Filter by minimum relevance score
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = AICitationAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        citations = AICitationService.get_by_filters(
            reasoning_log_id=str(validated_params.get('reasoning_log_id')) if validated_params.get('reasoning_log_id') else None,
            document_version_id=str(validated_params.get('document_version_id')) if validated_params.get('document_version_id') else None,
            min_relevance=validated_params.get('min_relevance'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to')
        )
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_citations, pagination_metadata = paginate_queryset(citations, page=page, page_size=page_size)
        
        return self.api_response(
            message="AI citations retrieved successfully.",
            data={
                'items': AICitationListSerializer(paginated_citations, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class AICitationAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed AI citation with full information.
    
    Endpoint: GET /api/v1/ai-decisions/admin/ai-citations/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
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


class AICitationAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete AI citation (for data cleanup/maintenance).
    
    Endpoint: DELETE /api/v1/ai-decisions/admin/ai-citations/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def delete(self, request, id):
        deleted = AICitationService.delete_citation(id)
        if not deleted:
            return self.api_response(
                message=f"AI citation with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="AI citation deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )
