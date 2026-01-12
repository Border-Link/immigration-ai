from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.rule_permission import RulePermission
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.serializers.visa_rule_version.read import VisaRuleVersionSerializer, VisaRuleVersionListSerializer
from main_system.utils import paginate_queryset


class VisaRuleVersionListAPI(AuthAPI):
    """Get list of visa rule versions. Supports filtering by visa_type_id."""
    permission_classes = [RulePermission]

    def get(self, request):
        visa_type_id = request.query_params.get('visa_type_id', None)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        if visa_type_id:
            rule_versions = VisaRuleVersionService.get_by_visa_type(visa_type_id)
        else:
            rule_versions = VisaRuleVersionService.get_all()

        # Paginate results
        paginated_items, pagination_metadata = paginate_queryset(rule_versions, page=page, page_size=page_size)

        return self.api_response(
            message="Visa rule versions retrieved successfully.",
            data={
                'items': VisaRuleVersionListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class VisaRuleVersionDetailAPI(AuthAPI):
    """Get visa rule version by ID."""
    permission_classes = [RulePermission]

    def get(self, request, id):
        rule_version = VisaRuleVersionService.get_by_id(id)
        if not rule_version:
            return self.api_response(
                message=f"Visa rule version with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa rule version retrieved successfully.",
            data=VisaRuleVersionSerializer(rule_version).data,
            status_code=status.HTTP_200_OK
        )

