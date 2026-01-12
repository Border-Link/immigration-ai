"""
Admin API Views for Case Status History Management

Admin-only endpoints for viewing case status history.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from immigration_cases.services.case_status_history_service import CaseStatusHistoryService
from immigration_cases.serializers.case_status_history.read import (
    CaseStatusHistoryListQuerySerializer,
    CaseStatusHistorySerializer,
    CaseStatusHistoryListSerializer
)
from main_system.utils import paginate_queryset

logger = logging.getLogger('django')


class CaseStatusHistoryListAPI(AuthAPI):
    """
    Admin: Get list of status history for a specific case.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/<case_id>/status-history/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request, case_id):
        # Validate query parameters
        query_serializer = CaseStatusHistoryListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        history = CaseStatusHistoryService.get_by_case_id(case_id)
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_history, pagination_metadata = paginate_queryset(history, page=page, page_size=page_size)
        
        return self.api_response(
            message=f"Status history for case {case_id} retrieved successfully.",
            data={
                'items': CaseStatusHistoryListSerializer(paginated_history, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class CaseStatusHistoryDetailAPI(AuthAPI):
    """
    Admin: Get detailed status history entry by ID.
    
    Endpoint: GET /api/v1/immigration-cases/admin/status-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request, id):
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
