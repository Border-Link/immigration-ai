"""
Admin API Views for Case Management

Admin-only endpoints for managing cases.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer, CaseListSerializer
from immigration_cases.serializers.case.admin import (
    CaseAdminUpdateSerializer,
    BulkCaseOperationSerializer,
)
from django.utils.dateparse import parse_datetime

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
        user_id = request.query_params.get('user_id', None)
        jurisdiction = request.query_params.get('jurisdiction', None)
        status_param = request.query_params.get('status', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        updated_date_from = request.query_params.get('updated_date_from', None)
        updated_date_to = request.query_params.get('updated_date_to', None)
        
        # Pagination parameters
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)
        
        try:
            cases = CaseService.get_by_filters(
                user_id=user_id,
                jurisdiction=jurisdiction,
                status=status_param,
                date_from=parse_datetime(date_from) if date_from else None,
                date_to=parse_datetime(date_to) if date_to else None,
                updated_date_from=parse_datetime(updated_date_from) if updated_date_from else None,
                updated_date_to=parse_datetime(updated_date_to) if updated_date_to else None,
            )
            
            # Paginate results
            paginated_cases, pagination_metadata = paginate_queryset(cases, page=page, page_size=page_size)
            
            return self.api_response(
                message="Cases retrieved successfully.",
                data={
                    'items': CaseListSerializer(paginated_cases, many=True).data,
                    'pagination': pagination_metadata
                },
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving cases: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving cases.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed case information.
    
    Endpoint: GET /api/v1/immigration-cases/admin/cases/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving case {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving case.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            case = CaseService.get_by_id(id)
            if not case:
                return self.api_response(
                    message=f"Case with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Extract version and reason for optimistic locking and history tracking
            version = serializer.validated_data.pop('version', None)
            reason = serializer.validated_data.pop('reason', None)
            
            updated_case = CaseService.update_case(
                id,
                updated_by_id=str(request.user.id) if request.user else None,
                reason=reason,
                version=version,
                **serializer.validated_data
            )
            
            if not updated_case:
                return self.api_response(
                    message=f"Case with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Case updated successfully.",
                data=CaseSerializer(updated_case).data,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_409_CONFLICT  # Conflict for optimistic locking or invalid transition
            )
        except Exception as e:
            logger.error(f"Error updating case {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating case.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CaseAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a case.
    
    Endpoint: DELETE /api/v1/immigration-cases/admin/cases/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            case = CaseService.get_by_id(id)
            if not case:
                return self.api_response(
                    message=f"Case with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = CaseService.delete_case(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting case.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Case deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting case {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting case.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            try:
                case = CaseService.get_by_id(str(case_id))
                if not case:
                    results['failed'].append({
                        'case_id': str(case_id),
                        'error': 'Case not found'
                    })
                    continue
                
                if operation == 'update_status':
                    if not status_value:
                        raise ValueError("status is required for 'update_status' operation.")
                    updated_case = CaseService.update_case(str(case_id), status=status_value)
                    if updated_case:
                        results['success'].append(CaseSerializer(updated_case).data)
                    else:
                        raise Exception("Failed to update case.")
                elif operation == 'delete':
                    deleted = CaseService.delete_case(str(case_id))
                    if deleted:
                        results['success'].append(str(case_id))
                    else:
                        raise Exception("Failed to delete case.")
                    continue # Skip serialization for deleted items
                elif operation == 'archive':
                    # Archive is essentially updating status to 'closed'
                    updated_case = CaseService.update_case(str(case_id), status='closed')
                    if updated_case:
                        results['success'].append(CaseSerializer(updated_case).data)
                    else:
                        raise Exception("Failed to archive case.")
                else:
                    raise ValueError(f"Invalid operation: {operation}")
            except Exception as e:
                results['failed'].append({
                    'case_id': str(case_id),
                    'error': str(e)
                })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
