from django.urls import path
from compliance.views import (
    AuditLogListAPI,
    AuditLogDetailAPI,
)

app_name = 'compliance'

urlpatterns = [
    # Audit Logs
    path('audit-logs/', AuditLogListAPI.as_view(), name='audit-logs-list'),
    path('audit-logs/<uuid:id>/', AuditLogDetailAPI.as_view(), name='audit-logs-detail'),
]

