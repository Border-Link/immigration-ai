# Data Ingestion Admin Functionality - Implementation Plan

## Overview

This document outlines the comprehensive admin functionality to be implemented for the `data_ingestion` directory, following the same architecture pattern as `users_access` and `ai_decisions`.

## Models Requiring Admin Functionality

1. **DataSource** - Configuration for monitored data sources
2. **SourceDocument** - Raw fetched content from data sources
3. **DocumentVersion** - Versioned extracted text from source documents
4. **DocumentChunk** - Document chunks with vector embeddings for RAG
5. **DocumentDiff** - Change detection between document versions
6. **ParsedRule** - AI-extracted rule candidates (staging area)
7. **RuleValidationTask** - Human validation tasks for parsed rules
8. **RuleParsingAuditLog** - Audit log for rule parsing operations

## Admin Functionality by Model

### 1. DataSource Admin
- ✅ List with filtering (jurisdiction, is_active, date range)
- ✅ Detail view
- ✅ Activate/Deactivate
- ✅ Delete
- ✅ Bulk operations (activate, deactivate, delete, trigger_ingestion)
- ✅ Trigger ingestion manually

### 2. SourceDocument Admin
- List with filtering (data_source_id, date range, http_status, has_error)
- Detail view
- Delete
- Bulk delete
- View raw content

### 3. DocumentVersion Admin
- List with filtering (source_document_id, date range)
- Detail view
- Delete
- Bulk delete
- View extracted text

### 4. DocumentChunk Admin
- List with filtering (document_version_id, has_embedding)
- Detail view
- Delete
- Bulk delete
- Re-embed chunks (regenerate embeddings)

### 5. DocumentDiff Admin
- List with filtering (change_type, date range)
- Detail view
- Delete
- Bulk delete

### 6. ParsedRule Admin
- List with filtering (status, visa_code, rule_type, confidence, date range)
- Detail view
- Update (status, confidence, description, excerpt)
- Delete
- Bulk operations (delete, approve, reject, mark_pending)

### 7. RuleValidationTask Admin
- List with filtering (status, assigned_to, date range, sla_deadline)
- Detail view
- Update (status, reviewer_notes, assigned_to)
- Assign to reviewer
- Approve/Reject
- Bulk operations (delete, assign, approve, reject, mark_pending)

### 8. RuleParsingAuditLog Admin
- List with filtering (action, status, error_type, date range, user)
- Detail view
- Analytics and reporting

## Analytics & Statistics Endpoints

1. **Ingestion Statistics**
   - Total data sources (active/inactive)
   - Documents fetched (by jurisdiction, by date)
   - Document versions created
   - Parsing success/failure rates
   - Token usage and cost tracking

2. **Validation Statistics**
   - Pending validation tasks
   - Approval/rejection rates
   - Average review time
   - SLA compliance

3. **Quality Metrics**
   - Average confidence scores
   - Citation quality
   - Embedding coverage

## Implementation Status

### Completed ✅
- Admin serializers created for all models
- DataSource admin views (list, detail, activate, delete, bulk operations)
- Serializer __init__.py files updated

### In Progress 🔄
- SourceDocument admin views
- DocumentVersion admin views
- DocumentChunk admin views
- ParsedRule admin views
- RuleValidationTask admin views

### Pending ⏳
- DocumentDiff admin views
- RuleParsingAuditLog admin views
- Analytics endpoints
- URL configuration
- Admin __init__.py updates

## File Structure

```
src/data_ingestion/
├── serializers/
│   ├── data_source/
│   │   └── admin.py ✅
│   ├── source_document/
│   │   └── admin.py ✅
│   ├── document_version/
│   │   └── admin.py ✅
│   ├── document_chunk/
│   │   └── admin.py ✅
│   ├── document_diff/
│   │   └── admin.py ✅
│   ├── parsed_rule/
│   │   └── admin.py ✅
│   └── rule_validation_task/
│       └── admin.py ✅
├── views/
│   └── admin/
│       ├── __init__.py ✅
│       ├── data_source_admin.py ✅
│       ├── source_document_admin.py ⏳
│       ├── document_version_admin.py ⏳
│       ├── document_chunk_admin.py ⏳
│       ├── document_diff_admin.py ⏳
│       ├── parsed_rule_admin.py ⏳
│       ├── rule_validation_task_admin.py ⏳
│       ├── audit_log_admin.py ⏳
│       └── ingestion_analytics.py ⏳
└── urls.py (needs admin routes) ⏳
```

## Next Steps

1. Complete remaining admin views
2. Add analytics endpoints
3. Update URLs
4. Update admin __init__.py
5. Test all endpoints
6. Update documentation
