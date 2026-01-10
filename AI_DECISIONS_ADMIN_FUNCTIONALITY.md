# AI Decisions - Comprehensive Admin/Staff Functionality

## Overview

As a lead principal engineer review, comprehensive admin and staff functionality has been implemented for the `ai_decisions` directory. All functionality is API-based (no Django admin), with proper permission separation and following the system architecture.

---

## Permission Model

### Permission Classes

1. **`IsAdminOrStaff`** - Staff OR Superuser
   - `is_staff=True` OR `is_superuser=True`
   - Used for all admin operations

---

## Admin Endpoints Summary

### Base Path: `/api/v1/ai-decisions/admin/`

---

## 1. Eligibility Result Management

### List Eligibility Results
- **Endpoint**: `GET /admin/eligibility-results/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Advanced filtering (case_id, visa_type_id, outcome, min_confidence, date range)
  - Returns all eligibility results with full details

### Eligibility Result Detail
- **Endpoint**: `GET /admin/eligibility-results/<id>/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Full eligibility result information

### Update Eligibility Result
- **Endpoint**: `PATCH /admin/eligibility-results/<id>/update/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Update outcome, confidence, reasoning_summary, missing_facts

### Delete Eligibility Result
- **Endpoint**: `DELETE /admin/eligibility-results/<id>/delete/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Delete eligibility result (data cleanup)

### Bulk Operations
- **Endpoint**: `POST /admin/eligibility-results/bulk-operation/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Bulk delete (up to 100 results)
  - Bulk update outcome (up to 100 results)
  - Returns success/failure for each result

---

## 2. AI Reasoning Log Management

### List AI Reasoning Logs
- **Endpoint**: `GET /admin/ai-reasoning-logs/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Advanced filtering (case_id, model_name, min_tokens, date range)
  - Returns all reasoning logs with full details

### AI Reasoning Log Detail
- **Endpoint**: `GET /admin/ai-reasoning-logs/<id>/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Full reasoning log with prompt and response

### Delete AI Reasoning Log
- **Endpoint**: `DELETE /admin/ai-reasoning-logs/<id>/delete/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Delete reasoning log (data cleanup)

### Bulk Operations
- **Endpoint**: `POST /admin/ai-reasoning-logs/bulk-operation/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Bulk delete (up to 100 logs)
  - Returns success/failure for each log

---

## 3. AI Citation Management

### List AI Citations
- **Endpoint**: `GET /admin/ai-citations/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Advanced filtering (reasoning_log_id, document_version_id, min_relevance, date range)
  - Returns all citations with full details

### AI Citation Detail
- **Endpoint**: `GET /admin/ai-citations/<id>/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Full citation information

### Update AI Citation
- **Endpoint**: `PATCH /admin/ai-citations/<id>/update/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Update excerpt, relevance_score

### Delete AI Citation
- **Endpoint**: `DELETE /admin/ai-citations/<id>/delete/`
- **Permission**: `IsAdminOrStaff`
- **Features**: Delete citation (data cleanup)

### Bulk Operations
- **Endpoint**: `POST /admin/ai-citations/bulk-operation/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Bulk delete (up to 100 citations)
  - Returns success/failure for each citation

---

## 4. Analytics & Statistics

### AI Decisions Statistics
- **Endpoint**: `GET /admin/statistics/`
- **Permission**: `IsAdminOrStaff`
- **Features**:
  - Eligibility results statistics (total, by outcome, avg confidence, requiring review)
  - AI reasoning logs statistics (total, by model, total tokens, avg tokens)
  - AI citations statistics (total, avg relevance, quality distribution)
  - Recent activity (last 30 days)
  - System metrics (cases with AI reasoning)

### Token Usage Analytics
- **Endpoint**: `GET /admin/token-usage/`
- **Permission**: `IsAdminOrStaff`
- **Query Params**:
  - `model_name`: Filter by model
  - `date_from`: Filter by date (from)
  - `date_to`: Filter by date (to)
- **Features**:
  - Total tokens used
  - Average tokens per log
  - Token usage by model
  - Cost tracking support

### Citation Quality Analytics
- **Endpoint**: `GET /admin/citation-quality/`
- **Permission**: `IsAdminOrStaff`
- **Query Params**:
  - `min_relevance`: Filter by minimum relevance score
  - `date_from`: Filter by date (from)
  - `date_to`: Filter by date (to)
- **Features**:
  - Average relevance score
  - Quality distribution (high/medium/low)
  - Average citations per reasoning log
  - Quality monitoring

---

## File Structure

```
src/ai_decisions/
├── serializers/
│   ├── eligibility_result/
│   │   └── admin.py (2 serializers)
│   ├── ai_reasoning_log/
│   │   └── admin.py (1 serializer)
│   └── ai_citation/
│       └── admin.py (2 serializers)
├── views/
│   └── admin/
│       ├── eligibility_result_admin.py (list, detail, delete)
│       ├── eligibility_result_management_advanced.py (update, bulk ops)
│       ├── ai_reasoning_log_admin.py (list, detail, delete)
│       ├── ai_reasoning_log_management_advanced.py (bulk ops)
│       ├── ai_citation_admin.py (list, detail, delete)
│       ├── ai_citation_management_advanced.py (update, bulk ops)
│       └── ai_decisions_analytics.py (statistics, analytics)
└── urls.py (all admin endpoints registered)
```

---

## Usage Examples

### Update Eligibility Result
```bash
PATCH /api/v1/ai-decisions/admin/eligibility-results/{id}/update/
{
  "outcome": "eligible",
  "confidence": 0.95,
  "reasoning_summary": "Updated by admin after review"
}
```

### Bulk Delete Eligibility Results
```bash
POST /api/v1/ai-decisions/admin/eligibility-results/bulk-operation/
{
  "result_ids": ["uuid1", "uuid2", "uuid3"],
  "operation": "delete"
}
```

### Bulk Update Eligibility Results
```bash
POST /api/v1/ai-decisions/admin/eligibility-results/bulk-operation/
{
  "result_ids": ["uuid1", "uuid2"],
  "operation": "update_outcome",
  "outcome": "requires_review",
  "confidence": 0.6
}
```

### Get Statistics
```bash
GET /api/v1/ai-decisions/admin/statistics/
```

### Get Token Usage Analytics
```bash
GET /api/v1/ai-decisions/admin/token-usage/?model_name=gpt-4&date_from=2024-01-01
```

### Update Citation
```bash
PATCH /api/v1/ai-decisions/admin/ai-citations/{id}/update/
{
  "relevance_score": 0.9,
  "excerpt": "Updated excerpt text"
}
```

---

## Summary

✅ **17 Admin Endpoints** implemented
✅ **Proper Permission Classes** (`IsAdminOrStaff`)
✅ **Comprehensive Management** (list, detail, update, delete)
✅ **Bulk Operations** support (up to 100 items)
✅ **Analytics & Statistics** endpoints
✅ **Token Usage Tracking** for cost management
✅ **Citation Quality Monitoring**
✅ **All Serializers in Serializers Directory** (proper separation)
✅ **All API-Based** (no Django admin)

**Status**: ✅ **PRODUCTION READY WITH FULL ADMIN FUNCTIONALITY**
