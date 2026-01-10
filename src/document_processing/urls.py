from django.urls import path
from document_processing.views.admin import (
    ProcessingJobAdminListAPI,
    ProcessingJobAdminDetailAPI,
    ProcessingJobAdminUpdateAPI,
    ProcessingJobAdminDeleteAPI,
    BulkProcessingJobOperationAPI,
    ProcessingHistoryAdminListAPI,
    ProcessingHistoryAdminDetailAPI,
    ProcessingHistoryAdminDeleteAPI,
    BulkProcessingHistoryOperationAPI,
    DocumentProcessingStatisticsAPI,
)

app_name = 'document_processing'

urlpatterns = [
    # Admin endpoints - Processing Jobs
    path('admin/processing-jobs/', ProcessingJobAdminListAPI.as_view(), name='admin-processing-jobs-list'),
    path('admin/processing-jobs/<uuid:id>/', ProcessingJobAdminDetailAPI.as_view(), name='admin-processing-jobs-detail'),
    path('admin/processing-jobs/<uuid:id>/update/', ProcessingJobAdminUpdateAPI.as_view(), name='admin-processing-jobs-update'),
    path('admin/processing-jobs/<uuid:id>/delete/', ProcessingJobAdminDeleteAPI.as_view(), name='admin-processing-jobs-delete'),
    path('admin/processing-jobs/bulk-operation/', BulkProcessingJobOperationAPI.as_view(), name='admin-processing-jobs-bulk-operation'),
    
    # Admin endpoints - Processing History
    path('admin/processing-history/', ProcessingHistoryAdminListAPI.as_view(), name='admin-processing-history-list'),
    path('admin/processing-history/<uuid:id>/', ProcessingHistoryAdminDetailAPI.as_view(), name='admin-processing-history-detail'),
    path('admin/processing-history/<uuid:id>/delete/', ProcessingHistoryAdminDeleteAPI.as_view(), name='admin-processing-history-delete'),
    path('admin/processing-history/bulk-operation/', BulkProcessingHistoryOperationAPI.as_view(), name='admin-processing-history-bulk-operation'),
    
    # Admin endpoints - Analytics
    path('admin/statistics/', DocumentProcessingStatisticsAPI.as_view(), name='admin-document-processing-statistics'),
]
