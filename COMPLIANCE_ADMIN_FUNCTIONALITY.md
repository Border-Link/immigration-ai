# Compliance - Comprehensive Admin/Staff Functionality

**Version:** 1.0  
**Date:** 2024  
**Status:** Complete Implementation

---

## Overview

This document describes the comprehensive admin functionality for the `compliance` directory. All admin operations are API-based (no Django admin interface), following the established system architecture pattern.

---

## Architecture Compliance

The compliance admin functionality follows the same architectural patterns as `data_ingestion`, `ai_decisions`, and `users_access`:

- ✅ **Serializers**: All serializers in `serializers/audit_log/admin.py`
- ✅ **Views**: All admin views in `views/admin/`
- ✅ **Services**: Business logic in `services/audit_log_service.py`
- ✅ **Selectors**: Read operations in `selectors/audit_log_selector.py`
- ✅ **Repositories**: Write operations in `repositories/audit_log_repository.py`
- ✅ **URLs**: All endpoints defined in `urls.py`
- ✅ **Permissions**: `IsAdminOrStaff` for all admin endpoints
- ✅ **No Django Admin**: `admin.py` file removed

---

## Models

### AuditLog

The compliance module manages general application audit logs (distinct from `data_ingestion.models.audit_log.RuleParsingAuditLog` which is domain-specific).

**Fields:**
- `id` (UUID, primary key)
- `level` (CharField) - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger_name` (CharField) - Logger name
- `message` (TextField) - Log message
- `timestamp` (DateTimeField) - Log timestamp
- `pathname` (TextField, nullable) - File path
- `lineno` (IntegerField, nullable) - Line number
- `func_name` (CharField, nullable) - Function name
- `process` (IntegerField, nullable) - Process ID
- `thread` (CharField, nullable) - Thread ID
- `created_at` (DateTimeField) - Creation timestamp
- `updated_at` (DateTimeField) - Last update timestamp

---

## Admin API Endpoints

All admin endpoints are prefixed with `/api/v1/compliance/admin/` and require `IsAdminOrStaff` permission.

### 1. Audit Log Management

#### 1.1 List Audit Logs (with Filtering)

**Endpoint:** `GET /api/v1/compliance/admin/audit-logs/`

**Query Parameters:**
- `level` (optional): Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger_name` (optional): Filter by logger name
- `date_from` (optional): Filter by timestamp (from) - ISO 8601 format
- `date_to` (optional): Filter by timestamp (to) - ISO 8601 format
- `limit` (optional): Limit number of results (default: no limit)

**Response:**
```json
{
    "message": "Audit logs retrieved successfully.",
    "data": [
        {
            "id": "uuid",
            "level": "ERROR",
            "logger_name": "django.request",
            "message": "Internal Server Error: /api/v1/...",
            "timestamp": "2024-01-01T12:00:00Z",
            "created_at": "2024-01-01T12:00:00Z"
        },
        ...
    ],
    "status_code": 200
}
```

**Example:**
```bash
GET /api/v1/compliance/admin/audit-logs/?level=ERROR&date_from=2024-01-01T00:00:00Z&limit=50
```

---

#### 1.2 Get Audit Log Detail

**Endpoint:** `GET /api/v1/compliance/admin/audit-logs/<id>/`

**Response:**
```json
{
    "message": "Audit log retrieved successfully.",
    "data": {
        "id": "uuid",
        "level": "ERROR",
        "logger_name": "django.request",
        "message": "Internal Server Error: /api/v1/...",
        "timestamp": "2024-01-01T12:00:00Z",
        "pathname": "/path/to/file.py",
        "lineno": 123,
        "func_name": "view_function",
        "process": 12345,
        "thread": "MainThread",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
    },
    "status_code": 200
}
```

---

#### 1.3 Delete Audit Log

**Endpoint:** `DELETE /api/v1/compliance/admin/audit-logs/<id>/delete/`

**Response:**
```json
{
    "message": "Audit log deleted successfully.",
    "data": null,
    "status_code": 200
}
```

**Error Response (404):**
```json
{
    "message": "Audit log with ID 'uuid' not found.",
    "data": null,
    "status_code": 404
}
```

---

#### 1.4 Bulk Delete Audit Logs

**Endpoint:** `POST /api/v1/compliance/admin/audit-logs/bulk-operation/`

**Request Body:**
```json
{
    "log_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "delete"
}
```

**Response:**
```json
{
    "message": "Bulk operation completed. Deleted: 3, Failed: 0.",
    "data": {
        "deleted_count": 3,
        "failed_count": 0,
        "total_requested": 3
    },
    "status_code": 200
}
```

**Validation:**
- `log_ids`: List of UUIDs (min: 1, max: 100)
- `operation`: Must be "delete"

---

### 2. Compliance Analytics

#### 2.1 Get Compliance Statistics

**Endpoint:** `GET /api/v1/compliance/admin/statistics/`

**Response:**
```json
{
    "message": "Compliance statistics retrieved successfully.",
    "data": {
        "audit_logs": {
            "total": 10000,
            "error_logs": 150,
            "by_level": [
                {"level": "INFO", "count": 8000},
                {"level": "WARNING", "count": 1850},
                {"level": "ERROR", "count": 140},
                {"level": "CRITICAL", "count": 10}
            ],
            "top_loggers": [
                {"logger_name": "django.request", "count": 5000},
                {"logger_name": "django.db.backends", "count": 3000},
                ...
            ],
            "recent_activity": {
                "last_24_hours": 500,
                "last_7_days": 3000,
                "last_30_days": 10000
            }
        }
    },
    "status_code": 200
}
```

**Statistics Include:**
- Total audit logs count
- Error logs count (ERROR + CRITICAL levels)
- Logs grouped by level
- Top 10 loggers by count
- Recent activity (24h, 7d, 30d)

---

## Reviewer/Admin Read-Only Endpoints

These endpoints are available to both reviewers and admins (read-only access):

### List Audit Logs (Basic)

**Endpoint:** `GET /api/v1/compliance/audit-logs/`

**Query Parameters:**
- `level` (optional): Filter by log level
- `logger_name` (optional): Filter by logger name
- `limit` (optional): Limit results (default: 100)

**Permission:** `IsAdminOrStaff`

---

### Get Audit Log Detail (Basic)

**Endpoint:** `GET /api/v1/compliance/audit-logs/<id>/`

**Permission:** `IsAdminOrStaff`

---

## Implementation Details

### Selectors (`selectors/audit_log_selector.py`)

**Methods:**
- `get_all()` - Get all audit logs
- `get_by_level(level)` - Get logs by level
- `get_by_logger_name(logger_name)` - Get logs by logger name
- `get_by_id(log_id)` - Get log by ID
- `get_recent(limit)` - Get recent logs
- `get_by_date_range(start_date, end_date)` - Get logs in date range
- `get_none()` - Get empty queryset
- `get_by_filters(...)` - Get logs with multiple filters
- `get_statistics()` - Get audit log statistics

### Repositories (`repositories/audit_log_repository.py`)

**Methods:**
- `create_audit_log(...)` - Create new audit log entry
- `delete_audit_log(audit_log)` - Delete audit log entry

### Services (`services/audit_log_service.py`)

**Methods:**
- `get_all()` - Get all audit logs
- `get_by_level(level)` - Get logs by level
- `get_by_logger_name(logger_name)` - Get logs by logger name
- `get_by_id(log_id)` - Get log by ID
- `get_recent(limit)` - Get recent logs
- `get_by_date_range(start_date, end_date)` - Get logs in date range
- `get_by_filters(...)` - Get logs with filters
- `get_statistics()` - Get statistics
- `delete_audit_log(log_id)` - Delete audit log

### Serializers (`serializers/audit_log/admin.py`)

- `AuditLogAdminListSerializer` - For list view
- `AuditLogAdminDetailSerializer` - For detail view
- `BulkAuditLogOperationSerializer` - For bulk operations

### Views (`views/admin/audit_log_admin.py`)

- `AuditLogAdminListAPI` - List with filtering
- `AuditLogAdminDetailAPI` - Detail view
- `AuditLogAdminDeleteAPI` - Delete single log
- `BulkAuditLogOperationAPI` - Bulk operations

### Analytics (`views/admin/compliance_analytics.py`)

- `ComplianceStatisticsAPI` - Statistics and analytics

---

## Security & Permissions

- **Admin Endpoints**: All require `IsAdminOrStaff` permission
- **Reviewer Endpoints**: Read-only access with `IsAdminOrStaff` permission
- **No Django Admin**: All admin functionality is API-based

---

## Error Handling

All endpoints include proper error handling:
- **400 Bad Request**: Invalid request data (validation errors)
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server errors (with logging)

---

## Usage Examples

### Filter Error Logs from Last 24 Hours

```bash
curl -X GET \
  "https://api.example.com/api/v1/compliance/admin/audit-logs/?level=ERROR&date_from=2024-01-01T00:00:00Z" \
  -H "Authorization: Bearer <token>"
```

### Delete Multiple Audit Logs

```bash
curl -X POST \
  "https://api.example.com/api/v1/compliance/admin/audit-logs/bulk-operation/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "log_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "delete"
  }'
```

### Get Compliance Statistics

```bash
curl -X GET \
  "https://api.example.com/api/v1/compliance/admin/statistics/" \
  -H "Authorization: Bearer <token>"
```

---

## Notes

1. **Audit Log Retention**: Consider implementing automatic cleanup of old audit logs based on retention policies.
2. **Performance**: For large datasets, consider adding pagination to list endpoints.
3. **Export**: Consider adding CSV/JSON export functionality for audit logs.
4. **Real-time Monitoring**: Consider adding WebSocket support for real-time log streaming.

---

## Related Documentation

- `DATA_INGESTION_ADMIN_IMPLEMENTATION_PLAN.md` - Reference implementation
- `AI_DECISIONS_ADMIN_FUNCTIONALITY.md` - Similar admin patterns
- `USERS_ACCESS_ADMIN_FUNCTIONALITY.md` - User management admin patterns
