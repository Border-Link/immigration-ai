"""
Admin API Views for Document Processing Analytics and Statistics

Admin-only endpoints for document processing analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.services.processing_history_service import ProcessingHistoryService

logger = logging.getLogger('django')


class DocumentProcessingStatisticsAPI(AuthAPI):
    """
    Admin: Get document processing statistics and analytics.
    
    Endpoint: GET /api/v1/document-processing/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        try:
            processing_job_stats = ProcessingJobService.get_statistics()
            processing_history_stats = ProcessingHistoryService.get_statistics()
            
            statistics = {
                'processing_jobs': processing_job_stats,
                'processing_history': processing_history_stats,
            }
            
            return self.api_response(
                message="Document processing statistics retrieved successfully.",
                data=statistics,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document processing statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document processing statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
