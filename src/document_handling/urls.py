from django.urls import path
from document_handling.views import (
    # Case Documents
    CaseDocumentCreateAPI,
    CaseDocumentListAPI,
    CaseDocumentDetailAPI,
    CaseDocumentVerifiedAPI,
    CaseDocumentUpdateAPI,
    CaseDocumentDeleteAPI,
    # Document Checks
    DocumentCheckCreateAPI,
    DocumentCheckListAPI,
    DocumentCheckDetailAPI,
    DocumentCheckUpdateAPI,
    DocumentCheckDeleteAPI,
)

app_name = 'document_handling'

urlpatterns = [
    # Case Documents
    path('case-documents/', CaseDocumentListAPI.as_view(), name='case-documents-list'),
    path('case-documents/create/', CaseDocumentCreateAPI.as_view(), name='case-documents-create'),
    path('case-documents/<uuid:id>/', CaseDocumentDetailAPI.as_view(), name='case-documents-detail'),
    path('case-documents/<uuid:id>/update/', CaseDocumentUpdateAPI.as_view(), name='case-documents-update'),
    path('case-documents/<uuid:id>/delete/', CaseDocumentDeleteAPI.as_view(), name='case-documents-delete'),
    path('case-documents/case/<uuid:case_id>/verified/', CaseDocumentVerifiedAPI.as_view(), name='case-documents-verified'),
    
    # Document Checks
    path('document-checks/', DocumentCheckListAPI.as_view(), name='document-checks-list'),
    path('document-checks/create/', DocumentCheckCreateAPI.as_view(), name='document-checks-create'),
    path('document-checks/<uuid:id>/', DocumentCheckDetailAPI.as_view(), name='document-checks-detail'),
    path('document-checks/<uuid:id>/update/', DocumentCheckUpdateAPI.as_view(), name='document-checks-update'),
    path('document-checks/<uuid:id>/delete/', DocumentCheckDeleteAPI.as_view(), name='document-checks-delete'),
]

