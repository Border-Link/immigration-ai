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
]

