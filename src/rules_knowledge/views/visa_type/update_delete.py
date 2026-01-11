import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_type_service import VisaTypeService
from rules_knowledge.serializers.visa_type.read import VisaTypeSerializer
from rules_knowledge.serializers.visa_type.update_delete import VisaTypeUpdateSerializer
from django.core.exceptions import ValidationError

logger = logging.getLogger('django')


class VisaTypeUpdateAPI(AuthAPI):
    """Update a visa type. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def patch(self, request, id):
        serializer = VisaTypeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            visa_type = VisaTypeService.update_visa_type(id, **serializer.validated_data)
            if not visa_type:
                return self.api_response(
                    message=f"Visa type with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )

            return self.api_response(
                message="Visa type updated successfully.",
                data=VisaTypeSerializer(visa_type).data,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating visa type {id}: {e}", exc_info=True)
            return self.api_response(
                message="An unexpected error occurred while updating visa type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VisaTypeDeleteAPI(AuthAPI):
    """Delete a visa type. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def delete(self, request, id):
        try:
            success = VisaTypeService.delete_visa_type(id)
            if not success:
                return self.api_response(
                    message=f"Visa type with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )

            return self.api_response(
                message="Visa type deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error deleting visa type {id}: {e}", exc_info=True)
            return self.api_response(
                message="An unexpected error occurred while deleting visa type.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

