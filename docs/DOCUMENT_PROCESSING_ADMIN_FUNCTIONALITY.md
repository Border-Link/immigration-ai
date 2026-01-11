# Document Processing - Comprehensive Admin/Staff Functionality

**Version:** 1.0  
**Date:** 2024  
**Status:** Complete Implementation

---

## Overview

This document describes the comprehensive admin functionality for the `document_processing` directory. All admin operations are API-based (no Django admin interface), following the established system architecture pattern.

The `document_processing` module tracks processing jobs, processing history, and provides analytics for document processing operations (OCR, classification, validation).

---

## Architecture Compliance

The document processing admin functionality follows the same architectural patterns as `data_ingestion`, `ai_decisions`, `users_access`, `compliance`, and `document_handling`:

- ✅ **Serializers**: All serializers in `serializers/processing_job/admin.py` and `serializers/processing_history/admin.py`
- ✅ **Views**: All admin views in `views/admin/`
- ✅ **Services**: Business logic in `services/processing_job_service.py` and `services/processing_history_service.py`
- ✅ **Selectors**: Read operations in `selectors/processing_job_selector.py` and `selectors/processing_history_selector.py`
- ✅ **Repositories**: Write operations in `repositories/processing_job_repository.py` and `repositories/processing_history_repository.py`
- ✅ **URLs**: All endpoints defined in `urls.py`
- ✅ **Permissions**: `IsAdminOrStaff` for all admin endpoints
- ✅ **No Django Admin**: `admin.py` file removed

---

## Models

### ProcessingJob

Tracks document processing jobs (OCR, classification, validation). Similar to how `data_ingestion` tracks ingestion jobs.

**Fields:**
- `id` (UUID, primary key)
- `case_document` (ForeignKey to CaseDocument)
- `processing_type` (CharField) - Type: ocr, classification, validation, full, reprocess
- `status` (CharField) - Status: pending, queued, processing, completed, failed, cancelled
- `celery_task_id` (CharField, nullable) - Celery task ID for tracking
- `priority` (IntegerField) - Job priority (1-10, higher is more urgent)
- `retry_count` (IntegerField) - Number of retry attempts
- `max_retries` (IntegerField) - Maximum number of retry attempts
- `error_message` (TextField, nullable) - Error message if processing failed
- `error_type` (CharField, nullable) - Type of error if processing failed
- `metadata` (JSONField, nullable) - Additional metadata (processing time, tokens used, cost, etc.)
- `started_at` (DateTimeField, nullable) - When processing started
- `completed_at` (DateTimeField, nullable) - When processing completed
- `created_by` (ForeignKey to User, nullable) - User who created this job (if manual)
- `created_at` (DateTimeField) - Creation timestamp
- `updated_at` (DateTimeField) - Last update timestamp

### ProcessingHistory

Audit log for document processing operations. Tracks all processing attempts, successes, failures, and metadata for compliance and operational excellence.

**Fields:**
- `id` (UUID, primary key)
- `case_document` (ForeignKey to CaseDocument)
- `processing_job` (ForeignKey to ProcessingJob, nullable) - Processing job this history entry belongs to
- `action` (CharField) - Action type (ocr_started, ocr_completed, classification_started, etc.)
- `user` (ForeignKey to User, nullable) - User who triggered the action (if applicable)
- `status` (CharField) - Status: success, failure, warning
- `message` (TextField, nullable) - Human-readable message
- `metadata` (JSONField, nullable) - Additional metadata (processing time, tokens, cost, confidence, etc.)
- `error_type` (CharField, nullable) - Error type if action failed
- `error_message` (TextField, nullable) - Error message if action failed
- `processing_time_ms` (IntegerField, nullable) - Processing time in milliseconds
- `created_at` (DateTimeField) - Creation timestamp

---

## Admin API Endpoints

All admin endpoints are prefixed with `/api/v1/document-processing/admin/` and require `IsAdminOrStaff` permission.

### 1. Processing Job Management

#### 1.1 List Processing Jobs (with Filtering)

**Endpoint:** `GET /api/v1/document-processing/admin/processing-jobs/`

**Query Parameters:**
- `case_document_id` (optional): Filter by case document ID
- `status` (optional): Filter by status (pending, queued, processing, completed, failed, cancelled)
- `processing_type` (optional): Filter by processing type (ocr, classification, validation, full, reprocess)
- `error_type` (optional): Filter by error type
- `created_by_id` (optional): Filter by creator ID
- `date_from` (optional): Filter by created date (from) - ISO 8601 format
- `date_to` (optional): Filter by created date (to) - ISO 8601 format
- `min_priority` (optional): Filter by minimum priority (1-10)
- `max_retries_exceeded` (optional): Filter by retry count exceeded (true/false)

**Response:**
```json
{
    "message": "Processing jobs retrieved successfully.",
    "data": [
        {
            "id": "uuid",
            "case_document_id": "uuid",
            "case_document_file_name": "passport.pdf",
            "case_id": "uuid",
            "processing_type": "full",
            "status": "completed",
            "priority": 5,
            "retry_count": 0,
            "max_retries": 3,
            "celery_task_id": "task-uuid",
            "created_by_email": "admin@example.com",
            "started_at": "2024-01-01T12:00:00Z",
            "completed_at": "2024-01-01T12:05:00Z",
            "created_at": "2024-01-01T12:00:00Z"
        },
        ...
    ],
    "status_code": 200
}
```

---

#### 1.2 Get Processing Job Detail

**Endpoint:** `GET /api/v1/document-processing/admin/processing-jobs/<id>/`

**Response:**
```json
{
    "message": "Processing job retrieved successfully.",
    "data": {
        "id": "uuid",
        "case_document_id": "uuid",
        "case_document_file_name": "passport.pdf",
        "case_document_status": "verified",
        "case_id": "uuid",
        "case_user_email": "user@example.com",
        "processing_type": "full",
        "status": "completed",
        "priority": 5,
        "retry_count": 0,
        "max_retries": 3,
        "celery_task_id": "task-uuid",
        "error_message": null,
        "error_type": null,
        "metadata": {
            "processing_time_ms": 300000,
            "tokens_used": 1500,
            "cost_usd": 0.015
        },
        "created_by_id": "uuid",
        "created_by_email": "admin@example.com",
        "started_at": "2024-01-01T12:00:00Z",
        "completed_at": "2024-01-01T12:05:00Z",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:05:00Z"
    },
    "status_code": 200
}
```

---

#### 1.3 Update Processing Job

**Endpoint:** `PUT /api/v1/document-processing/admin/processing-jobs/<id>/`

**Request Body:**
```json
{
    "status": "cancelled",
    "priority": 8,
    "max_retries": 5,
    "error_message": "Manual cancellation",
    "error_type": "manual",
    "metadata": {"reason": "User requested cancellation"}
}
```

**Response:**
```json
{
    "message": "Processing job updated successfully.",
    "data": { ... },
    "status_code": 200
}
```

---

#### 1.4 Delete Processing Job

**Endpoint:** `DELETE /api/v1/document-processing/admin/processing-jobs/<id>/`

**Response:**
```json
{
    "message": "Processing job deleted successfully.",
    "data": null,
    "status_code": 200
}
```

---

#### 1.5 Bulk Operations on Processing Jobs

**Endpoint:** `POST /api/v1/document-processing/admin/processing-jobs/bulk-operation/`

**Request Body:**
```json
{
    "job_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "delete",
    "status": "cancelled",  // Required if operation is "update_status"
    "priority": 8  // Required if operation is "update_priority"
}
```

**Operations:**
- `delete` - Delete multiple jobs
- `cancel` - Cancel multiple jobs (sets status to cancelled)
- `retry` - Retry failed jobs (resets failed jobs to pending)
- `update_status` - Update status for multiple jobs (requires `status` field)
- `update_priority` - Update priority for multiple jobs (requires `priority` field)

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

---

### 2. Processing History Management

#### 2.1 List Processing History (with Filtering)

**Endpoint:** `GET /api/v1/document-processing/admin/processing-history/`

**Query Parameters:**
- `case_document_id` (optional): Filter by case document ID
- `processing_job_id` (optional): Filter by processing job ID
- `action` (optional): Filter by action type
- `status` (optional): Filter by status (success, failure, warning)
- `error_type` (optional): Filter by error type
- `user_id` (optional): Filter by user ID
- `date_from` (optional): Filter by created date (from) - ISO 8601 format
- `date_to` (optional): Filter by created date (to) - ISO 8601 format
- `limit` (optional): Limit number of results

**Response:**
```json
{
    "message": "Processing history retrieved successfully.",
    "data": [
        {
            "id": "uuid",
            "case_document_id": "uuid",
            "case_document_file_name": "passport.pdf",
            "processing_job_id": "uuid",
            "action": "ocr_completed",
            "status": "success",
            "error_type": null,
            "processing_time_ms": 5000,
            "user_email": "system@example.com",
            "created_at": "2024-01-01T12:00:00Z"
        },
        ...
    ],
    "status_code": 200
}
```

---

#### 2.2 Get Processing History Detail

**Endpoint:** `GET /api/v1/document-processing/admin/processing-history/<id>/`

**Response:**
```json
{
    "message": "Processing history retrieved successfully.",
    "data": {
        "id": "uuid",
        "case_document_id": "uuid",
        "case_document_file_name": "passport.pdf",
        "case_id": "uuid",
        "processing_job_id": "uuid",
        "action": "ocr_completed",
        "status": "success",
        "message": "OCR extraction completed successfully",
        "metadata": {
            "pages": 1,
            "characters_extracted": 500,
            "confidence": 0.95
        },
        "error_type": null,
        "error_message": null,
        "processing_time_ms": 5000,
        "user_id": null,
        "user_email": null,
        "created_at": "2024-01-01T12:00:00Z"
    },
    "status_code": 200
}
```

---

#### 2.3 Delete Processing History Entry

**Endpoint:** `DELETE /api/v1/document-processing/admin/processing-history/<id>/`

**Response:**
```json
{
    "message": "Processing history entry deleted successfully.",
    "data": null,
    "status_code": 200
}
```

---

#### 2.4 Bulk Delete Processing History

**Endpoint:** `POST /api/v1/document-processing/admin/processing-history/bulk-operation/`

**Request Body:**
```json
{
    "history_ids": ["uuid1", "uuid2", "uuid3"],
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

---

### 3. Document Processing Analytics

#### 3.1 Get Document Processing Statistics

**Endpoint:** `GET /api/v1/document-processing/admin/statistics/`

**Response:**
```json
{
    "message": "Document processing statistics retrieved successfully.",
    "data": {
        "processing_jobs": {
            "total": 10000,
            "by_status": [
                {"status": "pending", "count": 100},
                {"status": "processing", "count": 50},
                {"status": "completed", "count": 9500},
                {"status": "failed", "count": 350}
            ],
            "by_type": [
                {"processing_type": "ocr", "count": 3000},
                {"processing_type": "classification", "count": 3000},
                {"processing_type": "validation", "count": 3000},
                {"processing_type": "full", "count": 1000}
            ],
            "failed": 350,
            "completed": 9500,
            "pending": 100,
            "processing": 50,
            "average_processing_time_ms": 125000.5,
            "with_errors": 350,
            "requiring_retry": 200,
            "exceeded_retries": 150,
            "recent_activity": {
                "last_24_hours": 500,
                "last_7_days": 3000,
                "last_30_days": 10000
            }
        },
        "processing_history": {
            "total": 50000,
            "by_action": [
                {"action": "ocr_started", "count": 5000},
                {"action": "ocr_completed", "count": 4800},
                {"action": "classification_started", "count": 5000},
                {"action": "classification_completed", "count": 4800},
                ...
            ],
            "by_status": [
                {"status": "success", "count": 45000},
                {"status": "failure", "count": 4000},
                {"status": "warning", "count": 1000}
            ],
            "failed": 4000,
            "successful": 45000,
            "warning": 1000,
            "with_errors": 4000,
            "average_processing_time_ms": 2500.5,
            "recent_activity": {
                "last_24_hours": 2500,
                "last_7_days": 15000,
                "last_30_days": 50000
            }
        }
    },
    "status_code": 200
}
```

**Statistics Include:**
- **Processing Jobs:**
  - Total count
  - Jobs by status
  - Jobs by processing type
  - Failed/completed/pending/processing counts
  - Average processing time
  - Jobs with errors
  - Jobs requiring retry
  - Jobs that exceeded max retries
  - Recent activity (24h, 7d, 30d)

- **Processing History:**
  - Total count
  - History entries by action
  - History entries by status
  - Failed/successful/warning counts
  - Entries with errors
  - Average processing time
  - Recent activity (24h, 7d, 30d)

---

## Implementation Details

### Selectors

**ProcessingJobSelector** (`selectors/processing_job_selector.py`):
- `get_all()` - Get all processing jobs
- `get_by_id(job_id)` - Get job by ID
- `get_by_case_document(case_document_id)` - Get jobs by case document
- `get_by_status(status)` - Get jobs by status
- `get_by_processing_type(processing_type)` - Get jobs by processing type
- `get_by_celery_task_id(celery_task_id)` - Get job by Celery task ID
- `get_pending()` - Get pending jobs (ordered by priority)
- `get_failed()` - Get failed jobs
- `get_none()` - Get empty queryset
- `get_by_filters(...)` - Get jobs with multiple filters
- `get_statistics()` - Get processing job statistics

**ProcessingHistorySelector** (`selectors/processing_history_selector.py`):
- `get_all()` - Get all processing history entries
- `get_by_id(history_id)` - Get history entry by ID
- `get_by_case_document(case_document_id)` - Get history by case document
- `get_by_processing_job(processing_job_id)` - Get history by processing job
- `get_by_action(action)` - Get history by action
- `get_by_status(status)` - Get history by status
- `get_none()` - Get empty queryset
- `get_by_filters(...)` - Get history with multiple filters
- `get_statistics()` - Get processing history statistics

### Repositories

**ProcessingJobRepository** (`repositories/processing_job_repository.py`):
- `create_processing_job(...)` - Create new processing job
- `update_processing_job(job, **fields)` - Update job fields
- `update_status(job, status)` - Update job status (auto-updates timestamps)
- `increment_retry_count(job)` - Increment retry count
- `delete_processing_job(job)` - Delete processing job

**ProcessingHistoryRepository** (`repositories/processing_history_repository.py`):
- `create_history_entry(...)` - Create new history entry
- `delete_history_entry(history)` - Delete history entry

### Services

**ProcessingJobService** (`services/processing_job_service.py`):
- `create_processing_job(...)` - Create new processing job
- `get_all()` - Get all processing jobs
- `get_by_id(job_id)` - Get job by ID
- `get_by_case_document(case_document_id)` - Get jobs by case document
- `get_by_status(status)` - Get jobs by status
- `get_by_processing_type(processing_type)` - Get jobs by processing type
- `get_by_celery_task_id(celery_task_id)` - Get job by Celery task ID
- `get_pending()` - Get pending jobs
- `get_failed()` - Get failed jobs
- `update_processing_job(job_id, **fields)` - Update job
- `update_status(job_id, status)` - Update job status
- `increment_retry_count(job_id)` - Increment retry count
- `delete_processing_job(job_id)` - Delete job
- `get_by_filters(...)` - Get jobs with filters
- `get_statistics()` - Get statistics

**ProcessingHistoryService** (`services/processing_history_service.py`):
- `create_history_entry(...)` - Create new history entry
- `get_all()` - Get all history entries
- `get_by_id(history_id)` - Get history entry by ID
- `get_by_case_document(case_document_id)` - Get history by case document
- `get_by_processing_job(processing_job_id)` - Get history by processing job
- `get_by_action(action)` - Get history by action
- `get_by_status(status)` - Get history by status
- `delete_history_entry(history_id)` - Delete history entry
- `get_by_filters(...)` - Get history with filters
- `get_statistics()` - Get statistics

### Serializers

**ProcessingJob Admin Serializers** (`serializers/processing_job/admin.py`):
- `ProcessingJobAdminListSerializer` - For list view
- `ProcessingJobAdminDetailSerializer` - For detail view
- `ProcessingJobAdminUpdateSerializer` - For update operations
- `BulkProcessingJobOperationSerializer` - For bulk operations

**ProcessingHistory Admin Serializers** (`serializers/processing_history/admin.py`):
- `ProcessingHistoryAdminListSerializer` - For list view
- `ProcessingHistoryAdminDetailSerializer` - For detail view
- `BulkProcessingHistoryOperationSerializer` - For bulk operations

### Views

**ProcessingJob Admin Views** (`views/admin/processing_job_admin.py`):
- `ProcessingJobAdminListAPI` - List with filtering
- `ProcessingJobAdminDetailAPI` - Detail view
- `ProcessingJobAdminUpdateAPI` - Update job
- `ProcessingJobAdminDeleteAPI` - Delete job
- `BulkProcessingJobOperationAPI` - Bulk operations

**ProcessingHistory Admin Views** (`views/admin/processing_history_admin.py`):
- `ProcessingHistoryAdminListAPI` - List with filtering
- `ProcessingHistoryAdminDetailAPI` - Detail view
- `ProcessingHistoryAdminDeleteAPI` - Delete history entry
- `BulkProcessingHistoryOperationAPI` - Bulk operations

**Analytics** (`views/admin/processing_analytics.py`):
- `DocumentProcessingStatisticsAPI` - Statistics and analytics

---

## Security & Permissions

- **Admin Endpoints**: All require `IsAdminOrStaff` permission
- **No Django Admin**: All admin functionality is API-based
- **Audit Trail**: All processing operations are logged in ProcessingHistory

---

## Error Handling

All endpoints include proper error handling:
- **400 Bad Request**: Invalid request data (validation errors)
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server errors (with logging)

---

## Usage Examples

### Filter Failed Processing Jobs

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-processing/admin/processing-jobs/?status=failed&date_from=2024-01-01T00:00:00Z" \
  -H "Authorization: Bearer <token>"
```

### Retry Failed Jobs in Bulk

```bash
curl -X POST \
  "https://api.example.com/api/v1/document-processing/admin/processing-jobs/bulk-operation/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "retry"
  }'
```

### Get Processing Statistics

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-processing/admin/statistics/" \
  -H "Authorization: Bearer <token>"
```

### View Processing History for a Document

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-processing/admin/processing-history/?case_document_id=uuid&limit=50" \
  -H "Authorization: Bearer <token>"
```

---

## Notes

1. **Job Tracking**: Processing jobs are automatically created when documents are uploaded and processing tasks are queued.
2. **History Logging**: All processing operations (OCR, classification, validation) should create history entries for audit purposes.
3. **Retry Logic**: Failed jobs can be retried if retry_count < max_retries.
4. **Priority System**: Jobs with higher priority are processed first.
5. **Celery Integration**: Jobs are linked to Celery tasks via `celery_task_id` for tracking.
6. **Performance**: For large datasets, consider adding pagination to list endpoints.

---

## Related Documentation

- `DATA_INGESTION_ADMIN_IMPLEMENTATION_PLAN.md` - Reference implementation
- `DOCUMENT_HANDLING_ADMIN_FUNCTIONALITY.md` - Document handling admin patterns
- `AI_DECISIONS_ADMIN_FUNCTIONALITY.md` - AI decisions admin patterns
- `USERS_ACCESS_ADMIN_FUNCTIONALITY.md` - User management admin patterns
- `COMPLIANCE_ADMIN_FUNCTIONALITY.md` - Compliance admin patterns
