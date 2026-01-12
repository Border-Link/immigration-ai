from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ingestion_permission import IngestionPermission
from data_ingestion.services.parsed_rule_service import ParsedRuleService
from data_ingestion.serializers.parsed_rule.read import (
    ParsedRuleSerializer,
    ParsedRuleListSerializer
)


class ParsedRuleListAPI(AuthAPI):
    """Get all parsed rules."""
    permission_classes = [IngestionPermission]

    def get(self, request):
        status_filter = request.query_params.get('status', None)
        visa_code = request.query_params.get('visa_code', None)
        
        if status_filter:
            parsed_rules = ParsedRuleService.get_by_status(status_filter)
        elif visa_code:
            parsed_rules = ParsedRuleService.get_by_visa_code(visa_code)
        else:
            parsed_rules = ParsedRuleService.get_all()

        return self.api_response(
            message="Parsed rules retrieved successfully.",
            data=ParsedRuleListSerializer(parsed_rules, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ParsedRuleDetailAPI(AuthAPI):
    """Get parsed rule by ID."""
    permission_classes = [IngestionPermission]

    def get(self, request, id):
        parsed_rule = ParsedRuleService.get_by_id(id)
        
        if not parsed_rule:
            return self.api_response(
                message=f"Parsed rule with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Parsed rule retrieved successfully.",
            data=ParsedRuleSerializer(parsed_rule).data,
            status_code=status.HTTP_200_OK
        )


class ParsedRulePendingAPI(AuthAPI):
    """Get all pending parsed rules."""
    permission_classes = [IngestionPermission]

    def get(self, request):
        parsed_rules = ParsedRuleService.get_pending()

        return self.api_response(
            message="Pending parsed rules retrieved successfully.",
            data=ParsedRuleListSerializer(parsed_rules, many=True).data,
            status_code=status.HTTP_200_OK
        )

