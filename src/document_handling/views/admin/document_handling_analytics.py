"""
Admin API Views for Document Handling Analytics and Statistics

Admin-only endpoints for document handling analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService

logger = logging.getLogger('django')


class DocumentHandlingStatisticsAPI(AuthAPI):
    """
    Admin: Get document handling statistics and analytics.
    
    Endpoint: GET /api/v1/document-handling/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        try:
            case_document_stats = CaseDocumentService.get_statistics()
            document_check_stats = DocumentCheckService.get_statistics()
            
            statistics = {
                'case_documents': case_document_stats,
                'document_checks': document_check_stats,
            }
            
            return self.api_response(
                message="Document handling statistics retrieved successfully.",
                data=statistics,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document handling statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document handling statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
