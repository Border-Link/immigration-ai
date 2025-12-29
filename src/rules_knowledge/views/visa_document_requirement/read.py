from rest_framework import status
from main_system.base.auth_api import AuthAPI
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from rules_knowledge.serializers.visa_document_requirement.read import (
    VisaDocumentRequirementSerializer,
    VisaDocumentRequirementListSerializer
)


class VisaDocumentRequirementListAPI(AuthAPI):
    """Get list of visa document requirements. Supports filtering by rule_version_id."""

    def get(self, request):
        rule_version_id = request.query_params.get('rule_version_id', None)

        if rule_version_id:
            doc_requirements = VisaDocumentRequirementService.get_by_rule_version(rule_version_id)
        else:
            doc_requirements = VisaDocumentRequirementService.get_all()

        return self.api_response(
            message="Visa document requirements retrieved successfully.",
            data=VisaDocumentRequirementListSerializer(doc_requirements, many=True).data,
            status_code=status.HTTP_200_OK
        )


class VisaDocumentRequirementDetailAPI(AuthAPI):
    """Get visa document requirement by ID."""

    def get(self, request, id):
        doc_requirement = VisaDocumentRequirementService.get_by_id(id)
        if not doc_requirement:
            return self.api_response(
                message=f"Visa document requirement with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Visa document requirement retrieved successfully.",
            data=VisaDocumentRequirementSerializer(doc_requirement).data,
            status_code=status.HTTP_200_OK
        )

