# Immigration Cases Admin Functionality

**Module**: `immigration_cases`  
**Status**: ✅ **FULLY IMPLEMENTED**  
**Date**: 2024

---

## Overview

The Immigration Cases module provides comprehensive admin functionality for managing cases and case facts through REST API endpoints. All admin operations are API-based (no Django admin), following the system's strict layered architecture.

---

## Architecture Compliance

The implementation strictly follows the system architecture:

- **Views** (`views/admin/`): API endpoints that handle HTTP requests/responses
  - Views call services only, no direct model access
  - All views use serializers for input validation and output formatting
  - Proper error handling with consistent response format
  - Permission-based access control (`IsAdminOrStaff`)

- **Services** (`services/`): Business logic layer
  - Services call selectors (read) and repositories (write)
  - No direct ORM access in services
  - All business logic encapsulated here
  - Audit logging integrated for all critical operations

- **Selectors** (`selectors/`): Read-only data access layer
  - All database read operations
  - Optimized queries with proper prefetching
  - Advanced filtering methods for admin functionality
  - No state mutations

- **Repositories** (`repositories/`): Write-only data access layer
  - All database write operations (create, update, delete)
  - Transaction management with `transaction.atomic()`
  - Proper validation and error handling

---

## Admin API Endpoints

### Base Path
All admin endpoints are under: `/api/v1/immigration-cases/admin/`

### Authentication & Authorization
- **Required**: Authentication token
- **Permission**: `IsAdminOrStaff` (staff OR superuser)

---

## Case Admin Endpoints

### 1. List Cases (with Advanced Filtering)
**Endpoint**: `GET /api/v1/immigration-cases/admin/cases/`

**Query Parameters**:
- `user_id` (optional): Filter by user ID
- `jurisdiction` (optional): Filter by jurisdiction (UK, US, CA, AU)
- `status` (optional): Filter by case status (draft, evaluated, awaiting_review, reviewed, closed)
- `date_from` (optional): Filter by created date (from) - ISO 8601 format
- `date_to` (optional): Filter by created date (to) - ISO 8601 format
- `updated_date_from` (optional): Filter by updated date (from) - ISO 8601 format
- `updated_date_to` (optional): Filter by updated date (to) - ISO 8601 format

**Response**:
```json
{
  "message": "Cases retrieved successfully.",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "user@example.com",
      "jurisdiction": "UK",
      "status": "evaluated",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "status_code": 200
}
```

### 2. Get Case Detail
**Endpoint**: `GET /api/v1/immigration-cases/admin/cases/<id>/`

**Response**:
```json
{
  "message": "Case retrieved successfully.",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user": "user-uuid",
    "user_email": "user@example.com",
    "jurisdiction": "UK",
    "status": "evaluated",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "status_code": 200
}
```

### 3. Update Case
**Endpoint**: `PATCH /api/v1/immigration-cases/admin/cases/<id>/update/`

**Request Body**:
```json
{
  "status": "reviewed",
  "jurisdiction": "UK"
}
```

**Response**: Same as Get Case Detail

### 4. Delete Case
**Endpoint**: `DELETE /api/v1/immigration-cases/admin/cases/<id>/delete/`

**Response**:
```json
{
  "message": "Case deleted successfully.",
  "data": null,
  "status_code": 200
}
```

### 5. Bulk Case Operations
**Endpoint**: `POST /api/v1/immigration-cases/admin/cases/bulk-operation/`

**Request Body**:
```json
{
  "case_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ],
  "operation": "update_status",
  "status": "reviewed"
}
```

**Operations**:
- `update_status`: Update status for multiple cases (requires `status` field)
- `delete`: Delete multiple cases
- `archive`: Archive multiple cases (sets status to 'closed')

**Response**:
```json
{
  "message": "Bulk operation 'update_status' completed. 2 succeeded, 0 failed.",
  "data": {
    "success": [...],
    "failed": []
  },
  "status_code": 200
}
```

---

## CaseFact Admin Endpoints

### 1. List Case Facts (with Advanced Filtering)
**Endpoint**: `GET /api/v1/immigration-cases/admin/case-facts/`

**Query Parameters**:
- `case_id` (optional): Filter by case ID
- `fact_key` (optional): Filter by fact key (e.g., 'salary', 'age', 'nationality')
- `source` (optional): Filter by source (user, ai, reviewer)
- `date_from` (optional): Filter by created date (from) - ISO 8601 format
- `date_to` (optional): Filter by created date (to) - ISO 8601 format

**Response**: Array of case fact objects

### 2. Get Case Fact Detail
**Endpoint**: `GET /api/v1/immigration-cases/admin/case-facts/<id>/`

**Response**: Single case fact object with full details

### 3. Update Case Fact
**Endpoint**: `PATCH /api/v1/immigration-cases/admin/case-facts/<id>/update/`

**Request Body**:
```json
{
  "fact_value": 50000,
  "source": "reviewer"
}
```

### 4. Delete Case Fact
**Endpoint**: `DELETE /api/v1/immigration-cases/admin/case-facts/<id>/delete/`

### 5. Bulk Case Fact Operations
**Endpoint**: `POST /api/v1/immigration-cases/admin/case-facts/bulk-operation/`

**Request Body**:
```json
{
  "case_fact_ids": ["...", "..."],
  "operation": "update_source",
  "source": "reviewer"
}
```

**Operations**:
- `delete`: Delete multiple case facts
- `update_source`: Update source for multiple case facts (requires `source` field)

---

## Statistics & Analytics

### Immigration Cases Statistics
**Endpoint**: `GET /api/v1/immigration-cases/admin/statistics/`

**Query Parameters**:
- `date_from` (optional): Filter by created date (from)
- `date_to` (optional): Filter by created date (to)

**Response**:
```json
{
  "message": "Immigration cases statistics retrieved successfully.",
  "data": {
    "cases": {
      "total_cases": 150,
      "draft_cases": 20,
      "evaluated_cases": 50,
      "awaiting_review_cases": 30,
      "reviewed_cases": 40,
      "closed_cases": 10,
      "cases_by_status": {
        "draft": 20,
        "evaluated": 50,
        "awaiting_review": 30,
        "reviewed": 40,
        "closed": 10
      },
      "cases_by_jurisdiction": {
        "UK": 100,
        "US": 30,
        "CA": 15,
        "AU": 5
      },
      "cases_by_user": {
        "user1@example.com": 10,
        "user2@example.com": 5
      }
    },
    "case_facts": {
      "total_facts": 500,
      "facts_by_source": {
        "user": 400,
        "ai": 80,
        "reviewer": 20
      },
      "facts_by_key": {
        "salary": 100,
        "age": 100,
        "nationality": 100
      }
    }
  },
  "status_code": 200
}
```

---

## Error Handling

All endpoints return consistent error responses:

**404 Not Found**:
```json
{
  "message": "Case with ID 'xxx' not found.",
  "data": null,
  "status_code": 404
}
```

**400 Bad Request** (Validation Error):
```json
{
  "message": "Validation error",
  "data": {
    "field_name": ["Error message"]
  },
  "status_code": 400
}
```

**500 Internal Server Error**:
```json
{
  "message": "Error retrieving cases.",
  "data": {
    "error": "Error message"
  },
  "status_code": 500
}
```

---

## Audit Logging

All critical operations are logged via `AuditLogService`:

- **Case Creation**: INFO level
- **Case Update**: INFO level (includes changed fields)
- **Case Deletion**: WARNING level
- **CaseFact Deletion**: WARNING level

Audit log failures are logged as warnings but do not break the operation (graceful degradation).

---

## Implementation Details

### Files Structure

```
src/immigration_cases/
├── serializers/
│   ├── case/
│   │   └── admin.py          # CaseAdminUpdateSerializer, BulkCaseOperationSerializer
│   └── case_fact/
│       └── admin.py          # CaseFactAdminUpdateSerializer, BulkCaseFactOperationSerializer
├── views/
│   └── admin/
│       ├── __init__.py
│       ├── case_admin.py     # Case admin views
│       ├── case_fact_admin.py # CaseFact admin views
│       └── immigration_cases_analytics.py # Statistics view
├── selectors/
│   ├── case_selector.py      # get_by_filters() method
│   └── case_fact_selector.py # get_by_filters() method
└── services/
    ├── case_service.py       # get_by_filters(), audit logging
    └── case_fact_service.py  # get_by_filters(), audit logging
```

### Key Features

1. **Advanced Filtering**: Comprehensive filtering capabilities in selectors and services
2. **Bulk Operations**: Efficient bulk operations for multiple cases/facts
3. **Statistics**: System-wide metrics and analytics
4. **Audit Logging**: All critical operations logged
5. **Transaction Management**: All write operations wrapped in transactions
6. **Error Handling**: Consistent error responses across all endpoints
7. **Permission Control**: `IsAdminOrStaff` permission class for all admin endpoints

---

## Testing Recommendations

1. **Unit Tests**: Test selectors, repositories, and services independently
2. **Integration Tests**: Test full request/response cycle for each endpoint
3. **Permission Tests**: Verify `IsAdminOrStaff` permission enforcement
4. **Filtering Tests**: Test all filter combinations
5. **Bulk Operation Tests**: Test bulk operations with various scenarios
6. **Error Handling Tests**: Test error scenarios (404, 400, 500)
7. **Audit Logging Tests**: Verify audit logs are created correctly

---

## Future Enhancements

- [ ] Soft delete for cases (instead of hard delete)
- [ ] Case status transition validation
- [ ] Optimistic locking for concurrent updates
- [ ] Case versioning/history tracking
- [ ] Advanced analytics (trends, predictions)
- [ ] Export functionality (CSV, PDF reports)

---

## Related Documentation

- `src/implementation.md` - System architecture and design
- `src/IMPLEMENTATION_STATUS.md` - Implementation status tracking
