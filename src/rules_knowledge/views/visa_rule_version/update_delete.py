import logging
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer
from rules_knowledge.serializers.visa_rule_version.update_delete import VisaRuleVersionUpdateSerializer

logger = logging.getLogger('django')


class VisaRuleVersionUpdateAPI(AuthAPI):
    """Update a visa rule version. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def patch(self, request, id):
        serializer = VisaRuleVersionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Extract version for optimistic locking if provided
            expected_version = serializer.validated_data.pop('version', None)
            updated_by = request.user if request.user.is_authenticated else None
            
            rule_version = VisaRuleVersionService.update_rule_version(
                id, updated_by=updated_by, expected_version=expected_version, **serializer.validated_data
            )
            
            if not rule_version:
                return self.api_response(
                    message=f"Visa rule version with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )

            return self.api_response(
                message="Visa rule version updated successfully.",
                data=VisaRuleVersionSerializer(rule_version).data,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            # Handle version conflicts (optimistic locking)
            if 'Version conflict' in str(e):
                return self.api_response(
                    message=str(e),
                    data={'error': 'version_conflict', 'detail': str(e)},
                    status_code=status.HTTP_409_CONFLICT
                )
            # Handle other validation errors
            return self.api_response(
                message=str(e),
                data={'error': 'validation_error', 'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating visa rule version {id}: {e}", exc_info=True)
            return self.api_response(
                message="An unexpected error occurred while updating visa rule version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaRuleVersionDeleteAPI(AuthAPI):
    """Delete a visa rule version. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def delete(self, request, id):
        success = VisaRuleVersionService.delete_visa_rule_version(id)
        if not success:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa rule version deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

