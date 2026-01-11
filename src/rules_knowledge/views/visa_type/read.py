from rest_framework import status
from main_system.base.auth_api import AuthAPI
from rules_knowledge.services.visa_type_service import VisaTypeService
from rules_knowledge.serializers.visa_type.read import VisaTypeSerializer, VisaTypeListSerializer
from rules_knowledge.helpers.pagination import paginate_queryset


class VisaTypeListAPI(AuthAPI):
    """Get list of visa types. Supports filtering by jurisdiction, is_active."""

    def get(self, request):
        jurisdiction = request.query_params.get('jurisdiction', None)
        is_active = request.query_params.get('is_active', None)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        if jurisdiction:
            visa_types = VisaTypeService.get_by_jurisdiction(jurisdiction)
        elif is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            if is_active_bool:
                visa_types = VisaTypeService.get_active()
            else:
                visa_types = VisaTypeService.get_all()
        else:
            visa_types = VisaTypeService.get_all()

        # Paginate results
        paginated_items, pagination_metadata = paginate_queryset(visa_types, page=page, page_size=page_size)

        return self.api_response(
            message="Visa types retrieved successfully.",
            data={
                'items': VisaTypeListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaTypeDetailAPI(AuthAPI):
    """Get visa type by ID."""

    def get(self, request, id):
        visa_type = VisaTypeService.get_by_id(id)
        if not visa_type:
            return self.api_response(
                message=f"Visa type with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa type retrieved successfully.",
            data=VisaTypeSerializer(visa_type).data,
            status_code=status.HTTP_200_OK
        )

