"""
View for document checklist generation.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from document_handling.services.document_checklist_service import DocumentChecklistService
from document_handling.serializers.case_document.checklist import DocumentChecklistSerializer
import logging

logger = logging.getLogger('django')


class DocumentChecklistAPI(AuthAPI):
    """Get document checklist for a case."""

    def get(self, request, case_id: str):
        """Get document checklist for a case."""
        try:
            checklist = DocumentChecklistService.generate_checklist(case_id)
            
            serializer = DocumentChecklistSerializer(checklist)
            
            return self.api_response(
                message="Document checklist retrieved successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document checklist: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document checklist.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
