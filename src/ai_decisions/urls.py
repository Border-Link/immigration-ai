from django.urls import path
from ai_decisions.views import (
    EligibilityResultCreateAPI,
    EligibilityResultListAPI,
    EligibilityResultDetailAPI,
    EligibilityResultUpdateAPI,
    EligibilityResultDeleteAPI,
    AIReasoningLogListAPI,
    AIReasoningLogDetailAPI,
    AICitationListAPI,
    AICitationDetailAPI,
)
from ai_decisions.views.admin import (
    EligibilityResultAdminListAPI,
    EligibilityResultAdminDetailAPI,
    EligibilityResultAdminDeleteAPI,
    EligibilityResultAdminUpdateAPI,
    BulkEligibilityResultOperationAPI,
    AIReasoningLogAdminListAPI,
    AIReasoningLogAdminDetailAPI,
    AIReasoningLogAdminDeleteAPI,
    BulkAIReasoningLogOperationAPI,
    AICitationAdminListAPI,
    AICitationAdminDetailAPI,
    AICitationAdminDeleteAPI,
    AICitationAdminUpdateAPI,
    BulkAICitationOperationAPI,
    AIDecisionsStatisticsAPI,
    TokenUsageAnalyticsAPI,
    CitationQualityAnalyticsAPI,
)

app_name = 'ai_decisions'

urlpatterns = [
    # Eligibility Result endpoints (standard user/reviewer access)
    path('eligibility-results/', EligibilityResultListAPI.as_view(), name='eligibility-result-list'),
    path('eligibility-results/create/', EligibilityResultCreateAPI.as_view(), name='eligibility-result-create'),
    path('eligibility-results/<uuid:id>/', EligibilityResultDetailAPI.as_view(), name='eligibility-result-detail'),
    path('eligibility-results/<uuid:id>/update/', EligibilityResultUpdateAPI.as_view(), name='eligibility-result-update'),
    path('eligibility-results/<uuid:id>/delete/', EligibilityResultDeleteAPI.as_view(), name='eligibility-result-delete'),
    
    # AI Reasoning Log endpoints (read-only, reviewer only)
    path('ai-reasoning-logs/', AIReasoningLogListAPI.as_view(), name='ai-reasoning-log-list'),
    path('ai-reasoning-logs/<uuid:id>/', AIReasoningLogDetailAPI.as_view(), name='ai-reasoning-log-detail'),
    
    # AI Citation endpoints (read-only, reviewer only)
    path('ai-citations/', AICitationListAPI.as_view(), name='ai-citation-list'),
    path('ai-citations/<uuid:id>/', AICitationDetailAPI.as_view(), name='ai-citation-detail'),
    
    # Admin endpoints (staff/superuser only)
    # Eligibility Results Admin
    path('admin/eligibility-results/', EligibilityResultAdminListAPI.as_view(), name='admin-eligibility-result-list'),
    path('admin/eligibility-results/bulk-operation/', BulkEligibilityResultOperationAPI.as_view(), name='admin-eligibility-result-bulk-operation'),
    path('admin/eligibility-results/<uuid:id>/', EligibilityResultAdminDetailAPI.as_view(), name='admin-eligibility-result-detail'),
    path('admin/eligibility-results/<uuid:id>/update/', EligibilityResultAdminUpdateAPI.as_view(), name='admin-eligibility-result-update'),
    path('admin/eligibility-results/<uuid:id>/delete/', EligibilityResultAdminDeleteAPI.as_view(), name='admin-eligibility-result-delete'),
    
    # AI Reasoning Logs Admin
    path('admin/ai-reasoning-logs/', AIReasoningLogAdminListAPI.as_view(), name='admin-ai-reasoning-log-list'),
    path('admin/ai-reasoning-logs/bulk-operation/', BulkAIReasoningLogOperationAPI.as_view(), name='admin-ai-reasoning-log-bulk-operation'),
    path('admin/ai-reasoning-logs/<uuid:id>/', AIReasoningLogAdminDetailAPI.as_view(), name='admin-ai-reasoning-log-detail'),
    path('admin/ai-reasoning-logs/<uuid:id>/delete/', AIReasoningLogAdminDeleteAPI.as_view(), name='admin-ai-reasoning-log-delete'),
    
    # AI Citations Admin
    path('admin/ai-citations/', AICitationAdminListAPI.as_view(), name='admin-ai-citation-list'),
    path('admin/ai-citations/bulk-operation/', BulkAICitationOperationAPI.as_view(), name='admin-ai-citation-bulk-operation'),
    path('admin/ai-citations/<uuid:id>/', AICitationAdminDetailAPI.as_view(), name='admin-ai-citation-detail'),
    path('admin/ai-citations/<uuid:id>/update/', AICitationAdminUpdateAPI.as_view(), name='admin-ai-citation-update'),
    path('admin/ai-citations/<uuid:id>/delete/', AICitationAdminDeleteAPI.as_view(), name='admin-ai-citation-delete'),
    
    # Analytics & Statistics
    path('admin/statistics/', AIDecisionsStatisticsAPI.as_view(), name='admin-statistics'),
    path('admin/token-usage/', TokenUsageAnalyticsAPI.as_view(), name='admin-token-usage'),
    path('admin/citation-quality/', CitationQualityAnalyticsAPI.as_view(), name='admin-citation-quality'),
]

