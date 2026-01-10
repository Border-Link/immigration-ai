"""
Admin API Views for AICitation Management

Admin-only endpoints for managing AI citations.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.serializers.ai_citation.read import AICitationSerializer, AICitationListSerializer

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
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        reasoning_log_id = request.query_params.get('reasoning_log_id', None)
        document_version_id = request.query_params.get('document_version_id', None)
        min_relevance = request.query_params.get('min_relevance', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            from django.utils.dateparse import parse_datetime
            
            # Parse parameters
            min_relevance_float = float(min_relevance) if min_relevance else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            citations = AICitationService.get_by_filters(
                reasoning_log_id=reasoning_log_id,
                document_version_id=document_version_id,
                min_relevance=min_relevance_float,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
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
                status_code=status.HTTP_400_BAD_REQUEST
            )


class AICitationAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed AI citation with full information.
    
    Endpoint: GET /api/v1/ai-decisions/admin/ai-citations/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
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
                status_code=status.HTTP_400_BAD_REQUEST
            )


class AICitationAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete AI citation (for data cleanup/maintenance).
    
    Endpoint: DELETE /api/v1/ai-decisions/admin/ai-citations/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            citation = AICitationService.get_by_id(id)
            if not citation:
                return self.api_response(
                    message=f"AI citation with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = AICitationService.delete_citation(id)
            if deleted:
                return self.api_response(
                    message="AI citation deleted successfully.",
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error deleting AI citation.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error deleting AI citation {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting AI citation.",
                data={'error': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
