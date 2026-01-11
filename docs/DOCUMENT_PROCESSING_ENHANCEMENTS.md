# Document Processing Enhancements - Expiry Date Extraction & Content Validation

**Version:** 1.0  
**Date:** 2024  
**Status:** Complete Implementation

---

## Overview

This document describes the implementation of the remaining document processing features:
1. **Document Expiry Date Extraction** - Extracts expiry dates from documents using AI/LLM
2. **Content Validation Against Case Facts** - Validates document content against case facts using AI/LLM

Both features are fully integrated into the document processing workflow and include comprehensive admin functionality.

---

## Implementation Summary

### 1. Document Expiry Date Extraction ✅ **FULLY IMPLEMENTED**

#### Service: `DocumentExpiryExtractionService`
**Location**: `src/document_handling/services/document_expiry_extraction_service.py`

**Features**:
- Extracts expiry dates from documents using LLM (OpenAI GPT-4o-mini)
- Supports multiple document types: passport, visa, certificate, license
- Handles various date formats (DD/MM/YYYY, YYYY-MM-DD, Month DD, YYYY, etc.)
- Returns expiry date, confidence score, and metadata
- Helper methods:
  - `is_expired(expiry_date, buffer_days=0)` - Check if expiry date has passed
  - `days_until_expiry(expiry_date)` - Calculate days until expiry

**Integration**:
- Integrated into `process_document_task` (Step 3)
- Automatically extracts expiry dates for passport, visa, certificate, license document types
- Stores expiry date in `CaseDocument.expiry_date` field
- Stores extraction metadata in `CaseDocument.extracted_metadata` field

**Model Changes**:
- Added `expiry_date` field to `CaseDocument` model (DateField, nullable, indexed)
- Added `extracted_metadata` field to `CaseDocument` model (JSONField, nullable)

**Admin Support**:
- Admin list serializer includes `expiry_date`, `is_expired`, `days_until_expiry`
- Admin detail serializer includes full expiry date information
- Admin update serializer supports updating `expiry_date`
- Admin endpoints support filtering by:
  - `has_expiry_date` (true/false)
  - `expiry_date_from` (ISO date)
  - `expiry_date_to` (ISO date)
  - `is_expired` (true/false)
- Statistics include expiry date metrics:
  - `with_expiry_date` - Count of documents with expiry dates
  - `expired` - Count of expired documents
  - `expiring_soon` - Count of documents expiring within 90 days

---

### 2. Content Validation Against Case Facts ✅ **FULLY IMPLEMENTED**

#### Service: `DocumentContentValidationService`
**Location**: `src/document_handling/services/document_content_validation_service.py`

**Features**:
- Validates document content against case facts using LLM (OpenAI GPT-4o-mini)
- Compares document content (from OCR) with case facts
- Validates:
  - Names (first name, last name, full name)
  - Dates (date of birth, issue dates)
  - Numbers (passport numbers, ID numbers, reference numbers)
  - Nationality/country codes
  - Other relevant identifiers
- Returns validation status: `passed`, `failed`, `warning`, `pending`
- Returns detailed results:
  - `matched_fields` - List of fields that match
  - `mismatched_fields` - List of fields with conflicts
  - `missing_fields` - List of expected fields not found
  - `confidence` - Confidence score (0.0 to 1.0)
  - `summary` - Human-readable summary

**Integration**:
- Integrated into `process_document_task` (Step 4)
- Automatically validates content after OCR and classification
- Creates `DocumentCheck` with `check_type='content_validation'`
- Stores validation results in:
  - `CaseDocument.content_validation_status` field
  - `CaseDocument.content_validation_details` field (JSONField)
- Updates document status based on validation results

**Model Changes**:
- Added `content_validation_status` field to `CaseDocument` model (CharField, choices: pending, passed, failed, warning)
- Added `content_validation_details` field to `CaseDocument` model (JSONField, nullable)
- Added `content_validation` to `DocumentCheck.CHECK_TYPE_CHOICES`

**Admin Support**:
- Admin list serializer includes `content_validation_status`
- Admin detail serializer includes `content_validation_status`, `content_validation_details`, `content_validation_summary`
- Admin update serializer supports updating `content_validation_status` and `content_validation_details`
- Admin endpoints support filtering by `content_validation_status` (pending, passed, failed, warning)
- Statistics include content validation metrics:
  - `by_status` - Count by validation status
  - `passed` - Count of passed validations
  - `failed` - Count of failed validations
  - `warning` - Count of warning validations

---

## Updated Document Processing Workflow

The document processing workflow now includes:

1. **OCR Extraction** → Store text
2. **AI Classification** → Update document_type_id
3. **Expiry Date Extraction** → Extract and store expiry date (for passport, visa, certificate, license)
4. **Content Validation** → Validate document content against case facts
5. **Requirement Matching** → Validate against visa requirements (placeholder)
6. **Status Update** → Update document status based on all checks

---

## Architecture Compliance

Both services follow the established system architecture:

- ✅ **Services**: Business logic in `services/` directory
- ✅ **Selectors**: Read operations use `CaseDocumentSelector` and `CaseFactSelector`
- ✅ **Repositories**: Write operations use `CaseDocumentRepository`
- ✅ **Views**: Admin views call services only
- ✅ **Serializers**: Proper error handling and validation
- ✅ **URLs**: All endpoints in `urls.py`
- ✅ **Permissions**: `IsAdminOrStaff` for admin endpoints

---

## API Endpoints

### Admin Endpoints (Updated)

**Case Document List** (`GET /api/v1/document-handling/admin/case-documents/`):
- New query parameters:
  - `has_expiry_date` (true/false)
  - `expiry_date_from` (ISO date)
  - `expiry_date_to` (ISO date)
  - `content_validation_status` (pending, passed, failed, warning)
  - `is_expired` (true/false)

**Case Document Detail** (`GET /api/v1/document-handling/admin/case-documents/<id>/`):
- Now includes:
  - `expiry_date`
  - `is_expired`
  - `days_until_expiry`
  - `extracted_metadata`
  - `content_validation_status`
  - `content_validation_details`
  - `content_validation_summary`

**Case Document Update** (`PUT /api/v1/document-handling/admin/case-documents/<id>/`):
- Can update:
  - `expiry_date`
  - `content_validation_status`
  - `content_validation_details`
  - `extracted_metadata`

**Statistics** (`GET /api/v1/document-handling/admin/statistics/`):
- Now includes:
  - `expiry_statistics`: with_expiry_date, expired, expiring_soon
  - `content_validation`: by_status, passed, failed, warning

---

## Usage Examples

### Filter Documents with Expired Passports

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-handling/admin/case-documents/?is_expired=true&document_type_id=passport-uuid" \
  -H "Authorization: Bearer <token>"
```

### Filter Documents with Failed Content Validation

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-handling/admin/case-documents/?content_validation_status=failed" \
  -H "Authorization: Bearer <token>"
```

### Get Documents Expiring Soon

```bash
curl -X GET \
  "https://api.example.com/api/v1/document-handling/admin/case-documents/?expiry_date_from=2024-01-01&expiry_date_to=2024-03-31" \
  -H "Authorization: Bearer <token>"
```

### Update Expiry Date Manually

```bash
curl -X PUT \
  "https://api.example.com/api/v1/document-handling/admin/case-documents/<id>/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "expiry_date": "2025-12-31"
  }'
```

---

## Error Handling

Both services include comprehensive error handling:
- **LLM API failures**: Graceful fallback, returns None with error message
- **Invalid date formats**: Returns error message, doesn't crash
- **Missing case facts**: Returns 'pending' status with appropriate message
- **Insufficient OCR text**: Returns error message, doesn't attempt validation

---

## Performance Considerations

- **LLM Calls**: Both services use GPT-4o-mini (cheaper model) for cost efficiency
- **Temperature**: Set to 0.1 for consistent, deterministic results
- **Token Limits**: OCR text is limited to 2000 characters to avoid token limits
- **Async Processing**: All processing happens in Celery tasks, not blocking API requests

---

## Testing Recommendations

1. **Expiry Date Extraction**:
   - Test with various date formats
   - Test with documents without expiry dates
   - Test with expired documents
   - Test with documents expiring soon

2. **Content Validation**:
   - Test with matching case facts
   - Test with mismatched case facts
   - Test with missing case facts
   - Test with partial matches

3. **Integration**:
   - Test full document processing workflow
   - Test status updates based on validation results
   - Test admin filtering and statistics

---

## Related Documentation

- `DOCUMENT_PROCESSING_ADMIN_FUNCTIONALITY.md` - Document processing admin functionality
- `DOCUMENT_HANDLING_ADMIN_FUNCTIONALITY.md` - Document handling admin functionality
- `DOCUMENT_PROCESSING_WORKFLOW.md` - Document processing workflow
- `implementation.md` - Section 8.4, 8.7.1, 8.7.2

---

## Migration Notes

**Important**: The new model fields require a database migration:

```bash
python manage.py makemigrations document_handling
python manage.py migrate
```

**New Fields**:
- `CaseDocument.expiry_date` (DateField, nullable)
- `CaseDocument.extracted_metadata` (JSONField, nullable)
- `CaseDocument.content_validation_status` (CharField, default='pending')
- `CaseDocument.content_validation_details` (JSONField, nullable)

**Updated Choices**:
- `DocumentCheck.CHECK_TYPE_CHOICES` - Added 'content_validation' and 'requirement_match'

---

## Notes

1. **LLM Dependency**: Both services require `OPENAI_API_KEY` in settings
2. **Cost**: Uses GPT-4o-mini for cost efficiency (cheaper than GPT-4)
3. **Accuracy**: LLM-based extraction and validation may have occasional errors - human review recommended for critical documents
4. **Performance**: Processing happens asynchronously in Celery tasks
5. **Scalability**: Services are stateless and can be horizontally scaled
