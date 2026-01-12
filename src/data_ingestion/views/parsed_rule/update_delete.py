from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ingestion_permission import IngestionPermission
from data_ingestion.services.parsed_rule_service import ParsedRuleService
from data_ingestion.serializers.parsed_rule.update_delete import (
    ParsedRuleUpdateSerializer,
    ParsedRuleStatusUpdateSerializer
)
from data_ingestion.serializers.parsed_rule.read import ParsedRuleSerializer


class ParsedRuleUpdateAPI(AuthAPI):
    """Update a parsed rule by ID."""
    permission_classes = [IngestionPermission]

    def patch(self, request, id):
        serializer = ParsedRuleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parsed_rule = ParsedRuleService.update_parsed_rule(id, **serializer.validated_data)

        if not parsed_rule:
            return self.api_response(
                message=f"Parsed rule with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Parsed rule updated successfully.",
            data=ParsedRuleSerializer(parsed_rule).data,
            status_code=status.HTTP_200_OK
        )


class ParsedRuleStatusUpdateAPI(AuthAPI):
    """Update parsed rule status by ID."""
    permission_classes = [IngestionPermission]

    def patch(self, request, id):
        serializer = ParsedRuleStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parsed_rule = ParsedRuleService.update_status(id, serializer.validated_data.get('status'))

        if not parsed_rule:
            return self.api_response(
                message=f"Parsed rule with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Parsed rule status updated successfully.",
            data=ParsedRuleSerializer(parsed_rule).data,
            status_code=status.HTTP_200_OK
        )

