from django.urls import path
from immigration_cases.views import (
    CaseCreateAPI,
    CaseListAPI,
    CaseDetailAPI,
    CaseUpdateAPI,
    CaseDeleteAPI,
    CaseEligibilityCheckAPI,
    CaseEligibilityExplanationAPI,
    CaseFactCreateAPI,
    CaseFactListAPI,
    CaseFactDetailAPI,
    CaseFactUpdateAPI,
    CaseFactDeleteAPI,
)
from immigration_cases.views.admin import (
    CaseAdminListAPI,
    CaseAdminDetailAPI,
    CaseAdminUpdateAPI,
    CaseAdminDeleteAPI,
    BulkCaseOperationAPI,
    CaseFactAdminListAPI,
    CaseFactAdminDetailAPI,
    CaseFactAdminUpdateAPI,
    CaseFactAdminDeleteAPI,
    BulkCaseFactOperationAPI,
    CaseStatusHistoryListAPI,
    CaseStatusHistoryDetailAPI,
    ImmigrationCasesStatisticsAPI,
)

app_name = 'immigration_cases'

urlpatterns = [
    # Case endpoints
    path('cases/', CaseListAPI.as_view(), name='case-list'),
    path('cases/create/', CaseCreateAPI.as_view(), name='case-create'),
    path('cases/<uuid:id>/', CaseDetailAPI.as_view(), name='case-detail'),
    path('cases/<uuid:id>/update/', CaseUpdateAPI.as_view(), name='case-update'),
    path('cases/<uuid:id>/delete/', CaseDeleteAPI.as_view(), name='case-delete'),
    
    # Eligibility endpoints (from implementation.md Section 4.3)
    path('cases/<uuid:id>/eligibility/', CaseEligibilityCheckAPI.as_view(), name='case-eligibility-check'),
    path('cases/<uuid:id>/eligibility/<uuid:result_id>/explanation/', CaseEligibilityExplanationAPI.as_view(), name='case-eligibility-explanation'),
    
    # CaseFact endpoints
    path('case-facts/', CaseFactListAPI.as_view(), name='case-fact-list'),
    path('case-facts/create/', CaseFactCreateAPI.as_view(), name='case-fact-create'),
    path('case-facts/<uuid:id>/', CaseFactDetailAPI.as_view(), name='case-fact-detail'),
    path('case-facts/<uuid:id>/update/', CaseFactUpdateAPI.as_view(), name='case-fact-update'),
    path('case-facts/<uuid:id>/delete/', CaseFactDeleteAPI.as_view(), name='case-fact-delete'),
    
    # Admin endpoints (staff/superuser only)
    # Case Admin
    path('admin/cases/', CaseAdminListAPI.as_view(), name='admin-case-list'),
    path('admin/cases/bulk-operation/', BulkCaseOperationAPI.as_view(), name='admin-case-bulk-operation'),
    path('admin/cases/<uuid:id>/', CaseAdminDetailAPI.as_view(), name='admin-case-detail'),
    path('admin/cases/<uuid:id>/update/', CaseAdminUpdateAPI.as_view(), name='admin-case-update'),
    path('admin/cases/<uuid:id>/delete/', CaseAdminDeleteAPI.as_view(), name='admin-case-delete'),
    
    # CaseFact Admin
    path('admin/case-facts/', CaseFactAdminListAPI.as_view(), name='admin-case-fact-list'),
    path('admin/case-facts/bulk-operation/', BulkCaseFactOperationAPI.as_view(), name='admin-case-fact-bulk-operation'),
    path('admin/case-facts/<uuid:id>/', CaseFactAdminDetailAPI.as_view(), name='admin-case-fact-detail'),
    path('admin/case-facts/<uuid:id>/update/', CaseFactAdminUpdateAPI.as_view(), name='admin-case-fact-update'),
    path('admin/case-facts/<uuid:id>/delete/', CaseFactAdminDeleteAPI.as_view(), name='admin-case-fact-delete'),
    
    # Case Status History Admin
    path('admin/cases/<uuid:case_id>/status-history/', CaseStatusHistoryListAPI.as_view(), name='admin-case-status-history'),
    path('admin/status-history/<uuid:id>/', CaseStatusHistoryDetailAPI.as_view(), name='admin-status-history-detail'),
    
    # Analytics & Statistics
    path('admin/statistics/', ImmigrationCasesStatisticsAPI.as_view(), name='admin-statistics'),
]

