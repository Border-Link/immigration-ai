"""
Admin API Views for RuleValidationTask Management

Admin-only endpoints for managing rule validation tasks.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
)
from data_ingestion.services.rule_validation_task_service import RuleValidationTaskService
from data_ingestion.serializers.rule_validation_task.read import (
    RuleValidationTaskSerializer,
    RuleValidationTaskListSerializer
)
from data_ingestion.serializers.rule_validation_task.admin import (
    RuleValidationTaskAdminListQuerySerializer,
    RuleValidationTaskAdminUpdateSerializer,
    BulkRuleValidationTaskOperationSerializer,
)


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
        query_serializer = RuleValidationTaskAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        tasks = RuleValidationTaskService.get_by_filters(
            status=query_serializer.validated_data.get('status'),
            assigned_to=str(query_serializer.validated_data.get('assigned_to')) if query_serializer.validated_data.get('assigned_to') else None,
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to'),
            sla_overdue=query_serializer.validated_data.get('sla_overdue')
        )
        
        return self.api_response(
            message="Rule validation tasks retrieved successfully.",
            data=RuleValidationTaskListSerializer(tasks, many=True).data,
            status_code=status.HTTP_200_OK
        )


class RuleValidationTaskAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed rule validation task information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/validation-tasks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Rule validation task"
    
    def get_entity_by_id(self, entity_id):
        """Get rule validation task by ID."""
        return RuleValidationTaskService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return RuleValidationTaskSerializer


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
        
        if not updated_task:
            return self.api_response(
                message="Error updating rule validation task.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return self.api_response(
            message="Rule validation task updated successfully.",
            data=RuleValidationTaskSerializer(updated_task).data,
            status_code=status.HTTP_200_OK
        )


class RuleValidationTaskAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete rule validation task.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/validation-tasks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Rule validation task"
    
    def get_entity_by_id(self, entity_id):
        """Get rule validation task by ID."""
        return RuleValidationTaskService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the rule validation task."""
        return RuleValidationTaskService.delete_validation_task(str(entity.id))


class BulkRuleValidationTaskOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on rule validation tasks.
    
    Endpoint: POST /api/v1/data-ingestion/admin/validation-tasks/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk rule validation task operation serializer."""
        return BulkRuleValidationTaskOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Rule validation task"
    
    def get_entity_by_id(self, entity_id):
        """Get rule validation task by ID."""
        return RuleValidationTaskService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the rule validation task."""
        assigned_to = validated_data.get('assigned_to')
        
        if operation == 'delete':
            return RuleValidationTaskService.delete_validation_task(str(entity.id))
        elif operation == 'assign':
            if not assigned_to:
                raise ValueError('assigned_to is required for assign operation')
            return RuleValidationTaskService.assign_reviewer(str(entity.id), str(assigned_to))
        elif operation == 'approve':
            return RuleValidationTaskService.approve_task(str(entity.id), auto_publish=False)
        elif operation == 'reject':
            return RuleValidationTaskService.reject_task(str(entity.id))
        elif operation == 'mark_pending':
            return RuleValidationTaskService.update_task(str(entity.id), status='pending')
        else:
            raise ValueError(f"Invalid operation: {operation}")
