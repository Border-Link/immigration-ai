"""
Admin API Views for Case Status History Management

Admin-only endpoints for viewing case status history.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from immigration_cases.services.case_status_history_service import CaseStatusHistoryService
from immigration_cases.serializers.case_status_history.read import CaseStatusHistorySerializer, CaseStatusHistoryListSerializer
from immigration_cases.helpers.pagination import paginate_queryset

logger = logging.getLogger('django')


class CaseStatusHistoryListAPI(AuthAPI):
    """
    Admin: Get list of status history for a specific case.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/<case_id>/status-history/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, case_id):
        try:
            history = CaseStatusHistoryService.get_by_case_id(case_id)
            
            # Pagination parameters
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 20)
            
            # Paginate results
            paginated_history, pagination_metadata = paginate_queryset(history, page=page, page_size=page_size)
            
            return self.api_response(
                message=f"Status history for case {case_id} retrieved successfully.",
                data={
                    'items': CaseStatusHistoryListSerializer(paginated_history, many=True).data,
                    'pagination': pagination_metadata
                },
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving status history for case {case_id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case status history.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseStatusHistoryDetailAPI(AuthAPI):
    """
    Admin: Get detailed status history entry by ID.
    
    Endpoint: GET /api/v1/immigration-cases/admin/status-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            history_entry = CaseStatusHistoryService.get_by_id(id)
            if not history_entry:
                return self.api_response(
                    message=f"Case status history entry with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Case status history entry retrieved successfully.",
                data=CaseStatusHistorySerializer(history_entry).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving case status history entry {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case status history entry.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
