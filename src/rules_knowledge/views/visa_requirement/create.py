import logging
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.serializers.visa_requirement.create import VisaRequirementCreateSerializer
from rules_knowledge.serializers.visa_requirement.read import VisaRequirementSerializer

logger = logging.getLogger('django')


class VisaRequirementCreateAPI(AuthAPI):
    """Create a new visa requirement. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = VisaRequirementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            requirement = VisaRequirementService.create_visa_requirement(
                rule_version_id=serializer.validated_data.get('rule_version_id'),
                requirement_code=serializer.validated_data.get('requirement_code'),
                description=serializer.validated_data.get('description'),
                condition_expression=serializer.validated_data.get('condition_expression'),
                is_active=serializer.validated_data.get('is_active', True)
            )

            if not requirement:
                return self.api_response(
                    message="Visa requirement already exists or error creating requirement.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            return self.api_response(
                message="Visa requirement created successfully.",
                data=VisaRequirementSerializer(requirement).data,
                status_code=status.HTTP_201_CREATED
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
            logger.error(f"Error creating visa requirement: {e}", exc_info=True)
            return self.api_response(
                message="An unexpected error occurred while creating visa requirement.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

