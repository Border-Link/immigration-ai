# Document Handling - Comprehensive Admin/Staff Functionality

**Version:** 1.0  
**Date:** 2024  
**Status:** Complete Implementation

---

## Overview

This document describes the comprehensive admin functionality for the `document_handling` directory. All admin operations are API-based (no Django admin interface), following the established system architecture pattern.

---

## Architecture Compliance

The document handling admin functionality follows the same architectural patterns as `data_ingestion`, `ai_decisions`, `users_access`, and `compliance`:

- ✅ **Serializers**: All serializers in `serializers/case_document/admin.py` and `serializers/document_check/admin.py`
- ✅ **Views**: All admin views in `views/admin/`
- ✅ **Services**: Business logic in `services/case_document_service.py` and `services/document_check_service.py`
- ✅ **Selectors**: Read operations in `selectors/case_document_selector.py` and `selectors/document_check_selector.py`
- ✅ **Repositories**: Write operations in `repositories/case_document_repository.py` and `repositories/document_check_repository.py`
- ✅ **URLs**: All endpoints defined in `urls.py`
- ✅ **Permissions**: `IsAdminOrStaff` for all admin endpoints
- ✅ **No Django Admin**: `admin.py` file removed

---

## Models

### CaseDocument

User-uploaded files for immigration cases. Documents are processed through OCR and validation.

**Fields:**
- `id` (UUID, primary key)
- `case` (ForeignKey to Case)
- `document_type` (ForeignKey to DocumentType)
- `file_path` (CharField) - Path to stored file
- `file_name` (CharField) - Original file name
- `file_size` (BigIntegerField, nullable) - File size in bytes
- `mime_type` (CharField, nullable) - MIME type
- `status` (CharField) - Status: uploaded, processing, verified, rejected
- `ocr_text` (TextField, nullable) - Extracted text from OCR
- `classification_confidence` (FloatField, nullable) - Confidence score (0.0 to 1.0)
- `uploaded_at` (DateTimeField) - Upload timestamp
- `updated_at` (DateTimeField) - Last update timestamp

### DocumentCheck

Automated and human validation results. Stores results of OCR, classification, and validation checks.

**Fields:**
- `id` (UUID, primary key)
- `case_document` (ForeignKey to CaseDocument)
- `check_type` (CharField) - Type: ocr, classification, validation, authenticity
- `result` (CharField) - Result: passed, failed, warning, pending
- `details` (JSONField, nullable) - Additional details
- `performed_by` (CharField, nullable) - Who/what performed the check
- `created_at` (DateTimeField) - Creation timestamp

---

## Admin API Endpoints

All admin endpoints are prefixed with `/api/v1/document-handling/admin/` and require `IsAdminOrStaff` permission.

### 1. Case Document Management

#### 1.1 List Case Documents (with Filtering)

**Endpoint:** `GET /api/v1/document-handling/admin/case-documents/`

**Query Parameters:**
- `case_id` (optional): Filter by case ID
- `document_type_id` (optional): Filter by document type ID
- `status` (optional): Filter by status (uploaded, processing, verified, rejected)
- `has_ocr_text` (optional): Filter by OCR text presence (true/false)
- `min_confidence` (optional): Filter by minimum classification confidence (0.0 to 1.0)
- `mime_type` (optional): Filter by MIME type
- `date_from` (optional): Filter by uploaded date (from) - ISO 8601 format
- `date_to` (optional): Filter by uploaded date (to) - ISO 8601 format

**Response:**
```json
{
    "message": "Case documents retrieved successfully.",
    "data": [
        {
            "id": "uuid",
            "case_id": "uuid",
            "case_user_email": "user@example.com",
            "document_type_name": "Passport",
            "file_name": "passport.pdf",
            "file_size": 1024000,
            "mime_type": "application/pdf",
            "status": "verified",
            "classification_confidence": 0.95,
            "has_ocr_text": true,
            "uploaded_at": "2024-01-01T12:00:00Z"
        },
        ...
    ],
    "status_code": 200
}
```

**Example:**
```bash
GET /api/v1/document-handling/admin/case-documents/?status=verified&has_ocr_text=true&min_confidence=0.8
```

---

#### 1.2 Get Case Document Detail

**Endpoint:** `GET /api/v1/document-handling/admin/case-documents/<id>/`

**Response:**
```json
{
    "message": "Case document retrieved successfully.",
    "data": {
        "id": "uuid",
        "case_id": "uuid",
        "case_user_email": "user@example.com",
        "case_user_id": "uuid",
        "document_type_id": "uuid",
        "document_type_name": "Passport",
        "file_path": "cases/uuid/document.pdf",
        "file_name": "passport.pdf",
        "file_size": 1024000,
        "mime_type": "application/pdf",
        "status": "verified",
        "ocr_text": "Extracted text...",
        "classification_confidence": 0.95,
        "uploaded_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
    },
    "status_code": 200
}
```

---

#### 1.3 Update Case Document

**Endpoint:** `PUT /api/v1/document-handling/admin/case-documents/<id>/`

**Request Body:**
```json
{
    "document_type_id": "uuid",
    "status": "verified",
    "classification_confidence": 0.95,
    "ocr_text": "Updated OCR text"
}
```

**Response:**
```json
{
    "message": "Case document updated successfully.",
    "data": { ... },
    "status_code": 200
}
```

---

#### 1.4 Delete Case Document

**Endpoint:** `DELETE /api/v1/document-handling/admin/case-documents/<id>/`

**Response:**
```json
{
    "message": "Case document deleted successfully.",
    "data": null,
    "status_code": 200
}
```

**Note:** This also deletes the stored file from storage.

---

#### 1.5 Bulk Operations on Case Documents

**Endpoint:** `POST /api/v1/document-handling/admin/case-documents/bulk-operation/`

**Request Body:**
```json
{
    "document_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "delete",
    "status": "verified"  // Required if operation is "update_status"
}
```

**Operations:**
- `delete` - Delete multiple documents
- `update_status` - Update status for multiple documents (requires `status` field)
- `reprocess_ocr` - Reprocess OCR (not yet implemented)
- `reprocess_classification` - Reprocess classification (not yet implemented)

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

### 2. Document Check Management

#### 2.1 List Document Checks (with Filtering)

**Endpoint:** `GET /api/v1/document-handling/admin/document-checks/`

**Query Parameters:**
- `case_document_id` (optional): Filter by case document ID
- `check_type` (optional): Filter by check type (ocr, classification, validation, authenticity)
- `result` (optional): Filter by result (passed, failed, warning, pending)
- `performed_by` (optional): Filter by who performed the check
- `date_from` (optional): Filter by created date (from) - ISO 8601 format
- `date_to` (optional): Filter by created date (to) - ISO 8601 format

**Response:**
```json
{
    "message": "Document checks retrieved successfully.",
    "data": [
        {
            "id": "uuid",
            "case_document_id": "uuid",
            "case_document_file_name": "passport.pdf",
            "case_id": "uuid",
            "check_type": "ocr",
            "result": "passed",
            "performed_by": "AI",
            "created_at": "2024-01-01T12:00:00Z"
        },
        ...
    ],
    "status_code": 200
}
```

---

#### 2.2 Get Document Check Detail

**Endpoint:** `GET /api/v1/document-handling/admin/document-checks/<id>/`

**Response:**
```json
{
    "message": "Document check retrieved successfully.",
    "data": {
        "id": "uuid",
        "case_document_id": "uuid",
        "case_document_file_name": "passport.pdf",
        "case_document_status": "verified",
        "case_id": "uuid",
        "case_user_email": "user@example.com",
        "check_type": "ocr",
        "result": "passed",
        "details": {"confidence": 0.95},
        "performed_by": "AI",
        "created_at": "2024-01-01T12:00:00Z"
    },
    "status_code": 200
}
```

---

#### 2.3 Update Document Check

**Endpoint:** `PUT /api/v1/document-handling/admin/document-checks/<id>/`

**Request Body:**
```json
{
    "result": "passed",
    "details": {"confidence": 0.95},
    "performed_by": "Human Reviewer"
}
```

**Response:**
```json
{
    "message": "Document check updated successfully.",
    "data": { ... },
    "status_code": 200
}
```

---

#### 2.4 Delete Document Check

**Endpoint:** `DELETE /api/v1/document-handling/admin/document-checks/<id>/`

**Response:**
```json
{
    "message": "Document check deleted successfully.",
    "data": null,
    "status_code": 200
}
```

---

#### 2.5 Bulk Delete Document Checks

**Endpoint:** `POST /api/v1/document-handling/admin/document-checks/bulk-operation/`

**Request Body:**
```json
{
    "check_ids": ["uuid1", "uuid2", "uuid3"],
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

### 3. Document Handling Analytics

#### 3.1 Get Document Handling Statistics

**Endpoint:** `GET /api/v1/document-handling/admin/statistics/`

**Response:**
```json
{
    "message": "Document handling statistics retrieved successfully.",
    "data": {
        "case_documents": {
            "total": 10000,
            "by_status": [
                {"status": "uploaded", "count": 1000},
                {"status": "processing", "count": 500},
                {"status": "verified", "count": 8000},
                {"status": "rejected", "count": 500}
            ],
            "with_ocr": 9500,
            "without_ocr": 500,
            "average_classification_confidence": 0.89,
            "total_file_size_bytes": 10737418240,
            "total_file_size_mb": 10240.0,
            "recent_activity": {
                "last_24_hours": 500,
                "last_7_days": 3000,
                "last_30_days": 10000
            },
            "by_document_type": [
                {"document_type": "Passport", "count": 3000},
                {"document_type": "Bank Statement", "count": 2500},
                ...
            ]
        },
        "document_checks": {
            "total": 50000,
            "by_type": [
                {"check_type": "ocr", "count": 15000},
                {"check_type": "classification", "count": 15000},
                {"check_type": "validation", "count": 15000},
                {"check_type": "authenticity", "count": 5000}
            ],
            "by_result": [
                {"result": "passed", "count": 40000},
                {"result": "failed", "count": 5000},
                {"result": "warning", "count": 3000},
                {"result": "pending", "count": 2000}
            ],
            "failed": 5000,
            "passed": 40000,
            "warning": 3000,
            "pending": 2000,
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
- **Case Documents:**
  - Total count
  - Documents by status
  - OCR coverage (with/without OCR text)
  - Average classification confidence
  - Total file size (bytes and MB)
  - Recent activity (24h, 7d, 30d)
  - Top 10 document types by count

- **Document Checks:**
  - Total count
  - Checks by type
  - Checks by result
  - Failed/passed/warning/pending counts
  - Recent activity (24h, 7d, 30d)

---

## Implementation Details

### Selectors

**CaseDocumentSelector** (`selectors/case_document_selector.py`):
- `get_all()` - Get all case documents
- `get_by_case(case)` - Get documents by case
- `get_by_status(status)` - Get documents by status
- `get_by_document_type(document_type_id)` - Get documents by document type
- `get_by_id(document_id)` - Get document by ID
- `get_verified_by_case(case)` - Get verified documents by case
- `get_none()` - Get empty queryset
- `get_by_filters(...)` - Get documents with multiple filters
- `get_statistics()` - Get case document statistics

**DocumentCheckSelector** (`selectors/document_check_selector.py`):
- `get_all()` - Get all document checks
- `get_by_case_document(case_document)` - Get checks by case document
- `get_by_check_type(check_type)` - Get checks by check type
- `get_by_result(result)` - Get checks by result
- `get_by_id(check_id)` - Get check by ID
- `get_latest_by_case_document(case_document, check_type)` - Get latest check
- `get_none()` - Get empty queryset
- `get_by_filters(...)` - Get checks with multiple filters
- `get_statistics()` - Get document check statistics

### Repositories

**CaseDocumentRepository** (`repositories/case_document_repository.py`):
- `create_case_document(...)` - Create new case document
- `update_case_document(case_document, **fields)` - Update document fields
- `update_status(case_document, status)` - Update document status
- `delete_case_document(case_document)` - Delete case document

**DocumentCheckRepository** (`repositories/document_check_repository.py`):
- `create_document_check(...)` - Create new document check
- `update_document_check(document_check, **fields)` - Update check fields
- `delete_document_check(document_check)` - Delete document check

### Services

**CaseDocumentService** (`services/case_document_service.py`):
- `create_case_document(...)` - Create new case document
- `get_all()` - Get all case documents
- `get_by_case(case_id)` - Get documents by case
- `get_by_status(status)` - Get documents by status
- `get_by_document_type(document_type_id)` - Get documents by document type
- `get_by_id(document_id)` - Get document by ID
- `update_case_document(document_id, **fields)` - Update document
- `update_status(document_id, status)` - Update document status
- `delete_case_document(document_id)` - Delete document (includes file deletion)
- `get_file_url(document_id)` - Get file access URL
- `get_verified_by_case(case_id)` - Get verified documents by case
- `get_by_filters(...)` - Get documents with filters
- `get_statistics()` - Get statistics

**DocumentCheckService** (`services/document_check_service.py`):
- `create_document_check(...)` - Create new document check
- `get_all()` - Get all document checks
- `get_by_case_document(case_document_id)` - Get checks by case document
- `get_by_check_type(check_type)` - Get checks by check type
- `get_by_result(result)` - Get checks by result
- `get_by_id(check_id)` - Get check by ID
- `update_document_check(check_id, **fields)` - Update check
- `delete_document_check(check_id)` - Delete check
- `get_latest_by_case_document(case_document_id, check_type)` - Get latest check
- `get_by_filters(...)` - Get checks with filters
- `get_statistics()` - Get statistics

### Serializers

**CaseDocument Admin Serializers** (`serializers/case_document/admin.py`):
- `CaseDocumentAdminListSerializer` - For list view
- `CaseDocumentAdminDetailSerializer` - For detail view
- `CaseDocumentAdminUpdateSerializer` - For update operations
- `BulkCaseDocumentOperationSerializer` - For bulk operations

**DocumentCheck Admin Serializers** (`serializers/document_check/admin.py`):
- `DocumentCheckAdminListSerializer` - For list view
- `DocumentCheckAdminDetailSerializer` - For detail view
- `DocumentCheckAdminUpdateSerializer` - For update operations
- `BulkDocumentCheckOperationSerializer` - For bulk operations

### Views

**CaseDocument Admin Views** (`views/admin/case_document_admin.py`):
- `CaseDocumentAdminListAPI` - List with filtering
- `CaseDocumentAdminDetailAPI` - Detail view
- `CaseDocumentAdminUpdateAPI` - Update document
- `CaseDocumentAdminDeleteAPI` - Delete document
- `BulkCaseDocumentOperationAPI` - Bulk operations

**DocumentCheck Admin Views** (`views/admin/document_check_admin.py`):
- `DocumentCheckAdminListAPI` - List with filtering
- `DocumentCheckAdminDetailAPI` - Detail view
- `DocumentCheckAdminUpdateAPI` - Update check
- `DocumentCheckAdminDeleteAPI` - Delete check
- `BulkDocumentCheckOperationAPI` - Bulk operations

**Analytics** (`views/admin/document_handling_analytics.py`):
- `DocumentHandlingStatisticsAPI` - Statistics and analytics

---

## Security & Permissions

- **Admin Endpoints**: All require `IsAdminOrStaff` permission
- **File Deletion**: When deleting case documents, associated files are also deleted from storage
- **No Django Admin**: All admin functionality is API-based

---

## Error Handling

All endpoints include proper error handling:
- **400 Bad Request**: Invalid request data (validation errors)
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server errors (with logging)
- **501 Not Implemented**: For operations not yet implemented (e.g., reprocess_ocr)

---

## Usage Examples

### Filter Verified Documents with OCR

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-handling/admin/case-documents/?status=verified&has_ocr_text=true" \
  -H "Authorization: Bearer <token>"
```

### Update Document Status in Bulk

```bash
curl -X POST \
  "https://api.example.com/api/v1/document-handling/admin/case-documents/bulk-operation/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["uuid1", "uuid2", "uuid3"],
    "operation": "update_status",
    "status": "verified"
  }'
```

### Get Document Handling Statistics

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-handling/admin/statistics/" \
  -H "Authorization: Bearer <token>"
```

### Filter Failed Checks

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-handling/admin/document-checks/?result=failed&date_from=2024-01-01T00:00:00Z" \
  -H "Authorization: Bearer <token>"
```

---

## Notes

1. **File Storage**: When deleting case documents, the associated files are automatically deleted from storage via `FileStorageService`.
2. **OCR Processing**: OCR reprocessing operations are planned but not yet implemented.
3. **Classification Reprocessing**: Classification reprocessing operations are planned but not yet implemented.
4. **Performance**: For large datasets, consider adding pagination to list endpoints.
5. **Export**: Consider adding CSV/JSON export functionality for documents and checks.

---

## Related Documentation

- `DATA_INGESTION_ADMIN_IMPLEMENTATION_PLAN.md` - Reference implementation
- `AI_DECISIONS_ADMIN_FUNCTIONALITY.md` - Similar admin patterns
- `USERS_ACCESS_ADMIN_FUNCTIONALITY.md` - User management admin patterns
- `COMPLIANCE_ADMIN_FUNCTIONALITY.md` - Compliance admin patterns
