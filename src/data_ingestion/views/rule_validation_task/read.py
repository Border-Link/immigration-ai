from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_validation_task_permission import RuleValidationTaskPermission
from data_ingestion.services.rule_validation_task_service import RuleValidationTaskService
from data_ingestion.serializers.rule_validation_task.read import (
    RuleValidationTaskSerializer,
    RuleValidationTaskListSerializer
)


class RuleValidationTaskListAPI(AuthAPI):
    """Get all rule validation tasks."""
    permission_classes = [RuleValidationTaskPermission]

    def get(self, request):
        status_filter = request.query_params.get('status', None)
        reviewer_id = request.query_params.get('reviewer_id', None)
        
        if status_filter:
            tasks = RuleValidationTaskService.get_by_status(status_filter)
        elif reviewer_id:
            tasks = RuleValidationTaskService.get_by_reviewer(reviewer_id)
        else:
            tasks = RuleValidationTaskService.get_all()

        return self.api_response(
            message="Rule validation tasks retrieved successfully.",
            data=RuleValidationTaskListSerializer(tasks, many=True).data,
            status_code=status.HTTP_200_OK
        )


class RuleValidationTaskDetailAPI(AuthAPI):
    """Get rule validation task by ID."""
    permission_classes = [RuleValidationTaskPermission]

    def get(self, request, id):
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


class RuleValidationTaskPendingAPI(AuthAPI):
    """Get all pending rule validation tasks."""
    permission_classes = [RuleValidationTaskPermission]

    def get(self, request):
        tasks = RuleValidationTaskService.get_pending()

        return self.api_response(
            message="Pending rule validation tasks retrieved successfully.",
            data=RuleValidationTaskListSerializer(tasks, many=True).data,
            status_code=status.HTTP_200_OK
        )

