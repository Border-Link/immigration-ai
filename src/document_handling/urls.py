from django.urls import path
from document_handling.views import (
    # Case Documents
    CaseDocumentCreateAPI,
    CaseDocumentListAPI,
    CaseDocumentDetailAPI,
    CaseDocumentVerifiedAPI,
    CaseDocumentUpdateAPI,
    CaseDocumentDeleteAPI,
    DocumentChecklistAPI,
    # Document Checks
    DocumentCheckCreateAPI,
    DocumentCheckListAPI,
    DocumentCheckDetailAPI,
    DocumentCheckUpdateAPI,
    DocumentCheckDeleteAPI,
)
from document_handling.views.admin import (
    CaseDocumentAdminListAPI,
    CaseDocumentAdminDetailAPI,
    CaseDocumentAdminUpdateAPI,
    CaseDocumentAdminDeleteAPI,
    BulkCaseDocumentOperationAPI,
    DocumentCheckAdminListAPI,
    DocumentCheckAdminDetailAPI,
    DocumentCheckAdminUpdateAPI,
    DocumentCheckAdminDeleteAPI,
    BulkDocumentCheckOperationAPI,
    DocumentHandlingStatisticsAPI,
)

app_name = 'document_handling'

urlpatterns = [
    # Case Documents (User/Reviewer endpoints)
    path('case-documents/', CaseDocumentListAPI.as_view(), name='case-documents-list'),
    path('case-documents/create/', CaseDocumentCreateAPI.as_view(), name='case-documents-create'),
    path('case-documents/<uuid:id>/', CaseDocumentDetailAPI.as_view(), name='case-documents-detail'),
    path('case-documents/<uuid:id>/update/', CaseDocumentUpdateAPI.as_view(), name='case-documents-update'),
    path('case-documents/<uuid:id>/delete/', CaseDocumentDeleteAPI.as_view(), name='case-documents-delete'),
    path('case-documents/case/<uuid:case_id>/verified/', CaseDocumentVerifiedAPI.as_view(), name='case-documents-verified'),
    path('case-documents/case/<uuid:case_id>/checklist/', DocumentChecklistAPI.as_view(), name='case-documents-checklist'),
    
    # Document Checks (User/Reviewer endpoints)
    path('document-checks/', DocumentCheckListAPI.as_view(), name='document-checks-list'),
    path('document-checks/create/', DocumentCheckCreateAPI.as_view(), name='document-checks-create'),
    path('document-checks/<uuid:id>/', DocumentCheckDetailAPI.as_view(), name='document-checks-detail'),
    path('document-checks/<uuid:id>/update/', DocumentCheckUpdateAPI.as_view(), name='document-checks-update'),
    path('document-checks/<uuid:id>/delete/', DocumentCheckDeleteAPI.as_view(), name='document-checks-delete'),
    
    # Admin endpoints - Case Documents
    path('admin/case-documents/', CaseDocumentAdminListAPI.as_view(), name='admin-case-documents-list'),
    path('admin/case-documents/<uuid:id>/', CaseDocumentAdminDetailAPI.as_view(), name='admin-case-documents-detail'),
    path('admin/case-documents/<uuid:id>/update/', CaseDocumentAdminUpdateAPI.as_view(), name='admin-case-documents-update'),
    path('admin/case-documents/<uuid:id>/delete/', CaseDocumentAdminDeleteAPI.as_view(), name='admin-case-documents-delete'),
    path('admin/case-documents/bulk-operation/', BulkCaseDocumentOperationAPI.as_view(), name='admin-case-documents-bulk-operation'),
    
    # Admin endpoints - Document Checks
    path('admin/document-checks/', DocumentCheckAdminListAPI.as_view(), name='admin-document-checks-list'),
    path('admin/document-checks/<uuid:id>/', DocumentCheckAdminDetailAPI.as_view(), name='admin-document-checks-detail'),
    path('admin/document-checks/<uuid:id>/update/', DocumentCheckAdminUpdateAPI.as_view(), name='admin-document-checks-update'),
    path('admin/document-checks/<uuid:id>/delete/', DocumentCheckAdminDeleteAPI.as_view(), name='admin-document-checks-delete'),
    path('admin/document-checks/bulk-operation/', BulkDocumentCheckOperationAPI.as_view(), name='admin-document-checks-bulk-operation'),
    
    # Admin endpoints - Analytics
    path('admin/statistics/', DocumentHandlingStatisticsAPI.as_view(), name='admin-document-handling-statistics'),
]

