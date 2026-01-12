"""
Admin API Views for Document Handling Analytics and Statistics

Admin-only endpoints for document handling analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService


class DocumentHandlingStatisticsAPI(AuthAPI):
    """
    Admin: Get document handling statistics and analytics.
    
    Endpoint: GET /api/v1/document-handling/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
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
