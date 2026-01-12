from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_validation_task_permission import RuleValidationTaskPermission
from data_ingestion.services.rule_validation_task_service import RuleValidationTaskService
from data_ingestion.serializers.rule_validation_task.update_delete import (
    RuleValidationTaskUpdateSerializer,
    RuleValidationTaskAssignSerializer,
    RuleValidationTaskApproveSerializer,
    RuleValidationTaskRejectSerializer
)
from data_ingestion.serializers.rule_validation_task.read import RuleValidationTaskSerializer


class RuleValidationTaskUpdateAPI(AuthAPI):
    """Update a rule validation task by ID."""
    permission_classes = [RuleValidationTaskPermission]

    def patch(self, request, id):
        serializer = RuleValidationTaskUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = RuleValidationTaskService.update_task(id, **serializer.validated_data)

        if not task:
            return self.api_response(
                message=f"Rule validation task with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Rule validation task updated successfully.",
            data=RuleValidationTaskSerializer(task).data,
            status_code=status.HTTP_200_OK
        )


class RuleValidationTaskAssignAPI(AuthAPI):
    """Assign a reviewer to a rule validation task."""
    permission_classes = [RuleValidationTaskPermission]

    def post(self, request, id):
        serializer = RuleValidationTaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = RuleValidationTaskService.assign_reviewer(
            id,
            serializer.validated_data.get('reviewer_id')
        )

        if not task:
            return self.api_response(
                message=f"Rule validation task with ID '{id}' not found or reviewer invalid.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Reviewer assigned successfully.",
            data=RuleValidationTaskSerializer(task).data,
            status_code=status.HTTP_200_OK
        )


class RuleValidationTaskApproveAPI(AuthAPI):
    """Approve a rule validation task."""
    permission_classes = [RuleValidationTaskPermission]

    def post(self, request, id):
        serializer = RuleValidationTaskApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = RuleValidationTaskService.approve_task(
            id,
            reviewer_notes=serializer.validated_data.get('reviewer_notes')
        )

        if not task:
            return self.api_response(
                message=f"Rule validation task with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Rule validation task approved successfully.",
            data=RuleValidationTaskSerializer(task).data,
            status_code=status.HTTP_200_OK
        )


class RuleValidationTaskRejectAPI(AuthAPI):
    """Reject a rule validation task."""
    permission_classes = [RuleValidationTaskPermission]

    def post(self, request, id):
        serializer = RuleValidationTaskRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = RuleValidationTaskService.reject_task(
            id,
            reviewer_notes=serializer.validated_data.get('reviewer_notes')
        )

        if not task:
            return self.api_response(
                message=f"Rule validation task with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Rule validation task rejected successfully.",
            data=RuleValidationTaskSerializer(task).data,
            status_code=status.HTTP_200_OK
        )

