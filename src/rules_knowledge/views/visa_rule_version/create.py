import logging
from rest_framework import status
from django.core.exceptions import ValidationError
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.create import VisaRuleVersionCreateSerializer
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer

logger = logging.getLogger('django')


class VisaRuleVersionCreateAPI(AuthAPI):
    """Create a new visa rule version. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = VisaRuleVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            created_by = request.user if request.user.is_authenticated else None
            rule_version = VisaRuleVersionService.create_rule_version(
                visa_type_id=serializer.validated_data.get('visa_type_id'),
                effective_from=serializer.validated_data.get('effective_from'),
                effective_to=serializer.validated_data.get('effective_to'),
                source_document_version_id=serializer.validated_data.get('source_document_version_id'),
                created_by=created_by
            )

            if not rule_version:
                return self.api_response(
                    message="Error creating visa rule version.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            return self.api_response(
                message="Visa rule version created successfully.",
                data=VisaRuleVersionSerializer(rule_version).data,
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
            logger.error(f"Error creating visa rule version: {e}", exc_info=True)
            return self.api_response(
                message="An unexpected error occurred while creating visa rule version.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

