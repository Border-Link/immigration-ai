from django.urls import path
from compliance.views import (
    AuditLogListAPI,
    AuditLogDetailAPI,
)
from compliance.views.admin import (
    AuditLogAdminListAPI,
    AuditLogAdminDetailAPI,
    AuditLogAdminDeleteAPI,
    BulkAuditLogOperationAPI,
    ComplianceStatisticsAPI,
)

app_name = 'compliance'

urlpatterns = [
    # Audit Logs (Reviewer/Admin read-only)
    path('audit-logs/', AuditLogListAPI.as_view(), name='audit-logs-list'),
    path('audit-logs/<uuid:id>/', AuditLogDetailAPI.as_view(), name='audit-logs-detail'),
    
    # Admin endpoints
    path('admin/audit-logs/', AuditLogAdminListAPI.as_view(), name='admin-audit-logs-list'),
    path('admin/audit-logs/<uuid:id>/', AuditLogAdminDetailAPI.as_view(), name='admin-audit-logs-detail'),
    path('admin/audit-logs/<uuid:id>/delete/', AuditLogAdminDeleteAPI.as_view(), name='admin-audit-logs-delete'),
    path('admin/audit-logs/bulk-operation/', BulkAuditLogOperationAPI.as_view(), name='admin-audit-logs-bulk-operation'),
    path('admin/statistics/', ComplianceStatisticsAPI.as_view(), name='admin-compliance-statistics'),
]

