from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.visa_type_service import VisaTypeService
from rules_knowledge.serializers.visa_type.create import VisaTypeCreateSerializer
from rules_knowledge.serializers.visa_type.read import VisaTypeSerializer


class VisaTypeCreateAPI(AuthAPI):
    """Create a new visa type. Only admin/staff can access."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = VisaTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        visa_type = VisaTypeService.create_visa_type(
            jurisdiction=serializer.validated_data.get('jurisdiction'),
            code=serializer.validated_data.get('code'),
            name=serializer.validated_data.get('name'),
            description=serializer.validated_data.get('description'),
            is_active=serializer.validated_data.get('is_active', True)
        )

        if not visa_type:
            return self.api_response(
                message="Visa type already exists or error creating visa type.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Visa type created successfully.",
            data=VisaTypeSerializer(visa_type).data,
            status_code=status.HTTP_201_CREATED
        )

