"""
Admin API Views for Case Management

Admin-only endpoints for managing cases.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer, CaseListSerializer
from immigration_cases.serializers.case.admin import (
    CaseAdminListQuerySerializer,
    CaseAdminUpdateSerializer,
    BulkCaseOperationSerializer,
)
from immigration_cases.helpers.pagination import paginate_queryset

logger = logging.getLogger('django')


class CaseAdminListAPI(AuthAPI):
    """
    Admin: Get list of all cases with advanced filtering.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/
    Auth: Required (staff/superuser only)
    Query Params:
        - user_id: Filter by user ID
        - jurisdiction: Filter by jurisdiction
        - status: Filter by case status
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - updated_date_from: Filter by updated date (from)
        - updated_date_to: Filter by updated date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = CaseAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        cases = CaseService.get_by_filters(
            user_id=str(validated_params.get('user_id')) if validated_params.get('user_id') else None,
            jurisdiction=validated_params.get('jurisdiction'),
            status=validated_params.get('status'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
            updated_date_from=validated_params.get('updated_date_from'),
            updated_date_to=validated_params.get('updated_date_to'),
        )
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_cases, pagination_metadata = paginate_queryset(cases, page=page, page_size=page_size)
        
        return self.api_response(
            message="Cases retrieved successfully.",
            data={
                'items': CaseListSerializer(paginated_cases, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class CaseAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed case information.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        case = CaseService.get_by_id(id)
        if not case:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Case retrieved successfully.",
            data=CaseSerializer(case).data,
            status_code=status.HTTP_200_OK
        )


class CaseAdminUpdateAPI(AuthAPI):
    """
    Admin: Update case status or jurisdiction.
    
    Endpoint: PATCH /api/v1/immigration-cases/admin/cases/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = CaseAdminUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Extract version and reason for optimistic locking and history tracking
        version = serializer.validated_data.pop('version', None)
        reason = serializer.validated_data.pop('reason', None)
        
        updated_case, error_message, http_status = CaseService.update_case(
            id,
            updated_by_id=str(request.user.id) if request.user else None,
            reason=reason,
            version=version,
            **serializer.validated_data
        )
        
        if not updated_case:
            status_code = status.HTTP_404_NOT_FOUND if http_status == 404 else (
                status.HTTP_409_CONFLICT if http_status == 409 else (
                    status.HTTP_400_BAD_REQUEST if http_status == 400 else status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            )
            return self.api_response(
                message=error_message or f"Case with ID '{id}' not found.",
                data=None,
                status_code=status_code
            )
        
        return self.api_response(
            message="Case updated successfully.",
            data=CaseSerializer(updated_case).data,
            status_code=status.HTTP_200_OK
        )


class CaseAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a case.
    
    Endpoint: DELETE /api/v1/immigration-cases/admin/cases/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = CaseService.delete_case(id)
        if not deleted:
            return self.api_response(
                message=f"Case with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Case deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )


class BulkCaseOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on cases (update_status, delete, archive).
    
    Endpoint: POST /api/v1/immigration-cases/admin/cases/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkCaseOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        case_ids = serializer.validated_data['case_ids']
        operation = serializer.validated_data['operation']
        status_value = serializer.validated_data.get('status')
        jurisdiction = serializer.validated_data.get('jurisdiction')
        
        results = {
            'success': [],
            'failed': []
        }
        
        for case_id in case_ids:
            case = CaseService.get_by_id(str(case_id))
            if not case:
                results['failed'].append({
                    'case_id': str(case_id),
                    'error': 'Case not found'
                })
                continue
            
            if operation == 'update_status':
                if not status_value:
                    results['failed'].append({
                        'case_id': str(case_id),
                        'error': "status is required for 'update_status' operation."
                    })
                    continue
                updated_case = CaseService.update_case(str(case_id), status=status_value)
                if updated_case:
                    results['success'].append(CaseSerializer(updated_case).data)
                else:
                    results['failed'].append({
                        'case_id': str(case_id),
                        'error': 'Failed to update case.'
                    })
            elif operation == 'delete':
                deleted = CaseService.delete_case(str(case_id))
                if deleted:
                    results['success'].append(str(case_id))
                else:
                    results['failed'].append({
                        'case_id': str(case_id),
                        'error': 'Failed to delete case.'
                    })
            elif operation == 'archive':
                # Archive is essentially updating status to 'closed'
                updated_case = CaseService.update_case(str(case_id), status='closed')
                if updated_case:
                    results['success'].append(CaseSerializer(updated_case).data)
                else:
                    results['failed'].append({
                        'case_id': str(case_id),
                        'error': 'Failed to archive case.'
                    })
            else:
                results['failed'].append({
                    'case_id': str(case_id),
                    'error': f"Invalid operation: {operation}"
                })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
