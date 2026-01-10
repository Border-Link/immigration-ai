from django.urls import path
from data_ingestion.views import (
    # Data Sources
    DataSourceCreateAPI,
    DataSourceListAPI,
    DataSourceDetailAPI,
    DataSourceUpdateAPI,
    DataSourceIngestionTriggerAPI,
    # Source Documents
    SourceDocumentListAPI,
    SourceDocumentDetailAPI,
    SourceDocumentLatestAPI,
    # Document Versions
    DocumentVersionListAPI,
    DocumentVersionDetailAPI,
    DocumentVersionLatestAPI,
    # Document Diffs
    DocumentDiffListAPI,
    DocumentDiffDetailAPI,
    # Parsed Rules
    ParsedRuleListAPI,
    ParsedRuleDetailAPI,
    ParsedRulePendingAPI,
    ParsedRuleUpdateAPI,
    ParsedRuleStatusUpdateAPI,
    # Rule Validation Tasks
    RuleValidationTaskListAPI,
    RuleValidationTaskDetailAPI,
    RuleValidationTaskPendingAPI,
    RuleValidationTaskUpdateAPI,
    RuleValidationTaskAssignAPI,
    RuleValidationTaskApproveAPI,
    RuleValidationTaskRejectAPI,
)
from data_ingestion.views.admin import (
    DataSourceAdminListAPI,
    DataSourceAdminDetailAPI,
    DataSourceAdminActivateAPI,
    DataSourceAdminDeleteAPI,
    BulkDataSourceOperationAPI,
    SourceDocumentAdminListAPI,
    SourceDocumentAdminDetailAPI,
    SourceDocumentAdminDeleteAPI,
    BulkSourceDocumentOperationAPI,
    DocumentVersionAdminListAPI,
    DocumentVersionAdminDetailAPI,
    DocumentVersionAdminDeleteAPI,
    BulkDocumentVersionOperationAPI,
    DocumentChunkAdminListAPI,
    DocumentChunkAdminDetailAPI,
    DocumentChunkAdminDeleteAPI,
    BulkDocumentChunkOperationAPI,
    DocumentDiffAdminListAPI,
    DocumentDiffAdminDetailAPI,
    DocumentDiffAdminDeleteAPI,
    BulkDocumentDiffOperationAPI,
    ParsedRuleAdminListAPI,
    ParsedRuleAdminDetailAPI,
    ParsedRuleAdminUpdateAPI,
    ParsedRuleAdminDeleteAPI,
    BulkParsedRuleOperationAPI,
    RuleValidationTaskAdminListAPI,
    RuleValidationTaskAdminDetailAPI,
    RuleValidationTaskAdminUpdateAPI,
    RuleValidationTaskAdminDeleteAPI,
    BulkRuleValidationTaskOperationAPI,
    RuleParsingAuditLogAdminListAPI,
    RuleParsingAuditLogAdminDetailAPI,
    IngestionStatisticsAPI,
    ParsingCostAnalyticsAPI,
)

app_name = 'data_ingestion'

urlpatterns = [
    # Data Sources
    path('data-sources/', DataSourceListAPI.as_view(), name='data-sources-list'),
    path('data-sources/create/', DataSourceCreateAPI.as_view(), name='data-sources-create'),
    path('data-sources/<uuid:id>/', DataSourceDetailAPI.as_view(), name='data-sources-detail'),
    path('data-sources/<uuid:id>/update/', DataSourceUpdateAPI.as_view(), name='data-sources-update'),
    path('data-sources/<uuid:id>/ingest/', DataSourceIngestionTriggerAPI.as_view(), name='data-sources-ingest'),
    
    # Source Documents
    path('source-documents/', SourceDocumentListAPI.as_view(), name='source-documents-list'),
    path('source-documents/<uuid:id>/', SourceDocumentDetailAPI.as_view(), name='source-documents-detail'),
    path('source-documents/data-source/<uuid:data_source_id>/latest/', SourceDocumentLatestAPI.as_view(), name='source-documents-latest'),
    
    # Document Versions
    path('document-versions/', DocumentVersionListAPI.as_view(), name='document-versions-list'),
    path('document-versions/<uuid:id>/', DocumentVersionDetailAPI.as_view(), name='document-versions-detail'),
    path('document-versions/source-document/<uuid:source_document_id>/latest/', DocumentVersionLatestAPI.as_view(), name='document-versions-latest'),
    
    # Document Diffs
    path('document-diffs/', DocumentDiffListAPI.as_view(), name='document-diffs-list'),
    path('document-diffs/<uuid:id>/', DocumentDiffDetailAPI.as_view(), name='document-diffs-detail'),
    
    # Parsed Rules
    path('parsed-rules/', ParsedRuleListAPI.as_view(), name='parsed-rules-list'),
    path('parsed-rules/pending/', ParsedRulePendingAPI.as_view(), name='parsed-rules-pending'),
    path('parsed-rules/<uuid:id>/', ParsedRuleDetailAPI.as_view(), name='parsed-rules-detail'),
    path('parsed-rules/<uuid:id>/update/', ParsedRuleUpdateAPI.as_view(), name='parsed-rules-update'),
    path('parsed-rules/<uuid:id>/status/', ParsedRuleStatusUpdateAPI.as_view(), name='parsed-rules-status'),
    
    # Rule Validation Tasks
    path('validation-tasks/', RuleValidationTaskListAPI.as_view(), name='validation-tasks-list'),
    path('validation-tasks/pending/', RuleValidationTaskPendingAPI.as_view(), name='validation-tasks-pending'),
    path('validation-tasks/<uuid:id>/', RuleValidationTaskDetailAPI.as_view(), name='validation-tasks-detail'),
    path('validation-tasks/<uuid:id>/update/', RuleValidationTaskUpdateAPI.as_view(), name='validation-tasks-update'),
    path('validation-tasks/<uuid:id>/assign/', RuleValidationTaskAssignAPI.as_view(), name='validation-tasks-assign'),
    path('validation-tasks/<uuid:id>/approve/', RuleValidationTaskApproveAPI.as_view(), name='validation-tasks-approve'),
    path('validation-tasks/<uuid:id>/reject/', RuleValidationTaskRejectAPI.as_view(), name='validation-tasks-reject'),
    
    # Admin endpoints (staff/superuser only)
    # Data Sources Admin
    path('admin/data-sources/', DataSourceAdminListAPI.as_view(), name='admin-data-sources-list'),
    path('admin/data-sources/bulk-operation/', BulkDataSourceOperationAPI.as_view(), name='admin-data-sources-bulk-operation'),
    path('admin/data-sources/<uuid:id>/', DataSourceAdminDetailAPI.as_view(), name='admin-data-sources-detail'),
    path('admin/data-sources/<uuid:id>/activate/', DataSourceAdminActivateAPI.as_view(), name='admin-data-sources-activate'),
    path('admin/data-sources/<uuid:id>/delete/', DataSourceAdminDeleteAPI.as_view(), name='admin-data-sources-delete'),
    
    # Source Documents Admin
    path('admin/source-documents/', SourceDocumentAdminListAPI.as_view(), name='admin-source-documents-list'),
    path('admin/source-documents/bulk-operation/', BulkSourceDocumentOperationAPI.as_view(), name='admin-source-documents-bulk-operation'),
    path('admin/source-documents/<uuid:id>/', SourceDocumentAdminDetailAPI.as_view(), name='admin-source-documents-detail'),
    path('admin/source-documents/<uuid:id>/delete/', SourceDocumentAdminDeleteAPI.as_view(), name='admin-source-documents-delete'),
    
    # Document Versions Admin
    path('admin/document-versions/', DocumentVersionAdminListAPI.as_view(), name='admin-document-versions-list'),
    path('admin/document-versions/bulk-operation/', BulkDocumentVersionOperationAPI.as_view(), name='admin-document-versions-bulk-operation'),
    path('admin/document-versions/<uuid:id>/', DocumentVersionAdminDetailAPI.as_view(), name='admin-document-versions-detail'),
    path('admin/document-versions/<uuid:id>/delete/', DocumentVersionAdminDeleteAPI.as_view(), name='admin-document-versions-delete'),
    
    # Document Chunks Admin
    path('admin/document-chunks/', DocumentChunkAdminListAPI.as_view(), name='admin-document-chunks-list'),
    path('admin/document-chunks/bulk-operation/', BulkDocumentChunkOperationAPI.as_view(), name='admin-document-chunks-bulk-operation'),
    path('admin/document-chunks/<uuid:id>/', DocumentChunkAdminDetailAPI.as_view(), name='admin-document-chunks-detail'),
    path('admin/document-chunks/<uuid:id>/delete/', DocumentChunkAdminDeleteAPI.as_view(), name='admin-document-chunks-delete'),
    
    # Document Diffs Admin
    path('admin/document-diffs/', DocumentDiffAdminListAPI.as_view(), name='admin-document-diffs-list'),
    path('admin/document-diffs/bulk-operation/', BulkDocumentDiffOperationAPI.as_view(), name='admin-document-diffs-bulk-operation'),
    path('admin/document-diffs/<uuid:id>/', DocumentDiffAdminDetailAPI.as_view(), name='admin-document-diffs-detail'),
    path('admin/document-diffs/<uuid:id>/delete/', DocumentDiffAdminDeleteAPI.as_view(), name='admin-document-diffs-delete'),
    
    # Parsed Rules Admin
    path('admin/parsed-rules/', ParsedRuleAdminListAPI.as_view(), name='admin-parsed-rules-list'),
    path('admin/parsed-rules/bulk-operation/', BulkParsedRuleOperationAPI.as_view(), name='admin-parsed-rules-bulk-operation'),
    path('admin/parsed-rules/<uuid:id>/', ParsedRuleAdminDetailAPI.as_view(), name='admin-parsed-rules-detail'),
    path('admin/parsed-rules/<uuid:id>/update/', ParsedRuleAdminUpdateAPI.as_view(), name='admin-parsed-rules-update'),
    path('admin/parsed-rules/<uuid:id>/delete/', ParsedRuleAdminDeleteAPI.as_view(), name='admin-parsed-rules-delete'),
    
    # Rule Validation Tasks Admin
    path('admin/validation-tasks/', RuleValidationTaskAdminListAPI.as_view(), name='admin-validation-tasks-list'),
    path('admin/validation-tasks/bulk-operation/', BulkRuleValidationTaskOperationAPI.as_view(), name='admin-validation-tasks-bulk-operation'),
    path('admin/validation-tasks/<uuid:id>/', RuleValidationTaskAdminDetailAPI.as_view(), name='admin-validation-tasks-detail'),
    path('admin/validation-tasks/<uuid:id>/update/', RuleValidationTaskAdminUpdateAPI.as_view(), name='admin-validation-tasks-update'),
    path('admin/validation-tasks/<uuid:id>/delete/', RuleValidationTaskAdminDeleteAPI.as_view(), name='admin-validation-tasks-delete'),
    
    # Audit Logs Admin
    path('admin/audit-logs/', RuleParsingAuditLogAdminListAPI.as_view(), name='admin-audit-logs-list'),
    path('admin/audit-logs/<uuid:id>/', RuleParsingAuditLogAdminDetailAPI.as_view(), name='admin-audit-logs-detail'),
    
    # Analytics & Statistics
    path('admin/statistics/', IngestionStatisticsAPI.as_view(), name='admin-statistics'),
    path('admin/cost-analytics/', ParsingCostAnalyticsAPI.as_view(), name='admin-cost-analytics'),
]

