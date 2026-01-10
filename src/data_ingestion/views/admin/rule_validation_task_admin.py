"""
Admin API Views for RuleValidationTask Management

Admin-only endpoints for managing rule validation tasks.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.rule_validation_task_service import RuleValidationTaskService
from data_ingestion.serializers.rule_validation_task.read import (
    RuleValidationTaskSerializer,
    RuleValidationTaskListSerializer
)
from data_ingestion.serializers.rule_validation_task.admin import (
    RuleValidationTaskAdminUpdateSerializer,
    BulkRuleValidationTaskOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class RuleValidationTaskAdminListAPI(AuthAPI):
    """
    Admin: Get list of all rule validation tasks with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/validation-tasks/
    Auth: Required (staff/superuser only)
    Query Params:
        - status: Filter by status
        - assigned_to: Filter by assigned reviewer ID
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - sla_overdue: Filter by overdue SLA tasks
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        status_filter = request.query_params.get('status', None)
        assigned_to = request.query_params.get('assigned_to', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        sla_overdue = request.query_params.get('sla_overdue', None)
        
        try:
            # Parse parameters
            sla_overdue_bool = sla_overdue.lower() == 'true' if sla_overdue is not None else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            tasks = RuleValidationTaskService.get_by_filters(
                status=status_filter,
                assigned_to=assigned_to,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                sla_overdue=sla_overdue_bool
            )
            
            return self.api_response(
                message="Rule validation tasks retrieved successfully.",
                data=RuleValidationTaskListSerializer(tasks, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving rule validation tasks: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving rule validation tasks.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RuleValidationTaskAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed rule validation task information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/validation-tasks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            task = RuleValidationTaskService.get_by_id(id)
            if not task:
                return self.api_response(
                    message=f"Rule validation task with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Rule validation task retrieved successfully.",
                data=RuleValidationTaskSerializer(task).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving rule validation task {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving rule validation task.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RuleValidationTaskAdminUpdateAPI(AuthAPI):
    """
    Admin: Update rule validation task.
    
    Endpoint: PATCH /api/v1/data-ingestion/admin/validation-tasks/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def patch(self, request, id):
        serializer = RuleValidationTaskAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            task = RuleValidationTaskService.get_by_id(id)
            if not task:
                return self.api_response(
                    message=f"Rule validation task with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            update_data = {}
            if 'status' in serializer.validated_data:
                update_data['status'] = serializer.validated_data['status']
            if 'reviewer_notes' in serializer.validated_data:
                update_data['reviewer_notes'] = serializer.validated_data['reviewer_notes']
            
            # Handle assigned_to separately if provided
            if 'assigned_to' in serializer.validated_data and serializer.validated_data['assigned_to']:
                # Assign reviewer using the service method
                reviewer_id = str(serializer.validated_data['assigned_to'])
                updated_task = RuleValidationTaskService.assign_reviewer(id, reviewer_id)
                if not updated_task:
                    return self.api_response(
                        message="Reviewer not found or failed to assign.",
                        data=None,
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                # Apply other updates if any
                if update_data:
                    updated_task = RuleValidationTaskService.update_task(id, **update_data)
            else:
                updated_task = RuleValidationTaskService.update_task(id, **update_data)
            
            if updated_task:
                return self.api_response(
                    message="Rule validation task updated successfully.",
                    data=RuleValidationTaskSerializer(updated_task).data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error updating rule validation task.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error updating rule validation task {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating rule validation task.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RuleValidationTaskAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete rule validation task.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/validation-tasks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            task = RuleValidationTaskService.get_by_id(id)
            if not task:
                return self.api_response(
                    message=f"Rule validation task with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = RuleValidationTaskService.delete_validation_task(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting rule validation task.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Rule validation task deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting rule validation task {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting rule validation task.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkRuleValidationTaskOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on rule validation tasks.
    
    Endpoint: POST /api/v1/data-ingestion/admin/validation-tasks/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkRuleValidationTaskOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        task_ids = serializer.validated_data['task_ids']
        operation = serializer.validated_data['operation']
        assigned_to = serializer.validated_data.get('assigned_to')
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for task_id in task_ids:
                try:
                    task = RuleValidationTaskService.get_by_id(str(task_id))
                    if not task:
                        results['failed'].append({
                            'task_id': str(task_id),
                            'error': 'Validation task not found'
                        })
                        continue
                    
                    if operation == 'delete':
                        deleted = RuleValidationTaskService.delete_validation_task(str(task_id))
                        if deleted:
                            results['success'].append(str(task_id))
                        else:
                            results['failed'].append({
                                'task_id': str(task_id),
                                'error': 'Failed to delete'
                            })
                    elif operation == 'assign':
                        if assigned_to:
                            updated = RuleValidationTaskService.assign_reviewer(str(task_id), str(assigned_to))
                            if updated:
                                results['success'].append(str(task_id))
                            else:
                                results['failed'].append({
                                    'task_id': str(task_id),
                                    'error': 'Failed to assign reviewer'
                                })
                        else:
                            results['failed'].append({
                                'task_id': str(task_id),
                                'error': 'assigned_to is required for assign operation'
                            })
                    elif operation == 'approve':
                        updated = RuleValidationTaskService.approve_task(str(task_id), auto_publish=False)
                        if updated:
                            results['success'].append(str(task_id))
                        else:
                            results['failed'].append({
                                'task_id': str(task_id),
                                'error': 'Failed to approve'
                            })
                    elif operation == 'reject':
                        updated = RuleValidationTaskService.reject_task(str(task_id))
                        if updated:
                            results['success'].append(str(task_id))
                        else:
                            results['failed'].append({
                                'task_id': str(task_id),
                                'error': 'Failed to reject'
                            })
                    elif operation == 'mark_pending':
                        updated = RuleValidationTaskService.update_task(str(task_id), status='pending')
                        if updated:
                            results['success'].append(str(task_id))
                        else:
                            results['failed'].append({
                                'task_id': str(task_id),
                                'error': 'Failed to mark pending'
                            })
                except Exception as e:
                    results['failed'].append({
                        'task_id': str(task_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
