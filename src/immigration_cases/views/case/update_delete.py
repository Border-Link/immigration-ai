from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from immigration_cases.services.case_service import CaseService
from immigration_cases.serializers.case.read import CaseSerializer
from immigration_cases.serializers.case.update_delete import CaseUpdateSerializer
import logging

logger = logging.getLogger('django')


class CaseUpdateAPI(AuthAPI):
    """Update a case."""

    def patch(self, request, id):
        serializer = CaseUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Extract version and reason for optimistic locking and history tracking
            version = serializer.validated_data.pop('version', None)
            reason = serializer.validated_data.pop('reason', None)
            
            case = CaseService.update_case(
                id,
                updated_by_id=str(request.user.id) if request.user else None,
                reason=reason,
                version=version,
                **serializer.validated_data
            )
            
            if not case:
                return self.api_response(
                    message=f"Case with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )

            return self.api_response(
                message="Case updated successfully.",
                data=CaseSerializer(case).data,
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


class CaseDeleteAPI(AuthAPI):
    """Delete a case."""

    def delete(self, request, id):
        success = CaseService.delete_case(id)
        if not success:
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

