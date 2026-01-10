"""
Admin views for document_processing module.
"""
from .processing_job_admin import (
    ProcessingJobAdminListAPI,
    ProcessingJobAdminDetailAPI,
    ProcessingJobAdminUpdateAPI,
    ProcessingJobAdminDeleteAPI,
    BulkProcessingJobOperationAPI,
)
from .processing_history_admin import (
    ProcessingHistoryAdminListAPI,
    ProcessingHistoryAdminDetailAPI,
    ProcessingHistoryAdminDeleteAPI,
    BulkProcessingHistoryOperationAPI,
)
from .processing_analytics import DocumentProcessingStatisticsAPI

__all__ = [
    'ProcessingJobAdminListAPI',
    'ProcessingJobAdminDetailAPI',
    'ProcessingJobAdminUpdateAPI',
    'ProcessingJobAdminDeleteAPI',
    'BulkProcessingJobOperationAPI',
    'ProcessingHistoryAdminListAPI',
    'ProcessingHistoryAdminDetailAPI',
    'ProcessingHistoryAdminDeleteAPI',
    'BulkProcessingHistoryOperationAPI',
    'DocumentProcessingStatisticsAPI',
]
