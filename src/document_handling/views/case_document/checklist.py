"""
View for document checklist generation.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.document_permission import DocumentPermission
from document_handling.services.document_checklist_service import DocumentChecklistService
from document_handling.serializers.case_document.checklist import DocumentChecklistSerializer


class DocumentChecklistAPI(AuthAPI):
    """Get document checklist for a case."""
    permission_classes = [DocumentPermission]

    def get(self, request, case_id: str):
        """Get document checklist for a case."""
        checklist = DocumentChecklistService.generate_checklist(case_id)
        
        if not checklist:
            return self.api_response(
                message="Error retrieving document checklist.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = DocumentChecklistSerializer(checklist)
        
        return self.api_response(
            message="Document checklist retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
