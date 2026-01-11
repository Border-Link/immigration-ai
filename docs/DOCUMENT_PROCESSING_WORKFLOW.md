# Document Processing Workflow

## Overview

This document explains how document upload, OCR, content extraction, and categorization work in the system, as per `implementation.md` Section 8.

## Complete Workflow

```
1. User Uploads Document
   ↓
2. File Stored (Local or S3)
   ↓
3. CaseDocument Record Created (status: 'uploaded')
   ↓
4. Signal Triggers Async Processing
   ↓
5. Celery Task: process_document_task
   ├─→ Step 1: OCR Extraction
   │   ├─→ Extract text from document
   │   ├─→ Store in ocr_text field
   │   └─→ Create OCR check
   │
   ├─→ Step 2: Document Classification
   │   ├─→ Use LLM to analyze OCR text
   │   ├─→ Predict document type
   │   ├─→ If confidence >= 0.7: Auto-update document_type_id
   │   ├─→ If confidence < 0.7: Flag for human review
   │   └─→ Create classification check
   │
   └─→ Step 3: Requirement Matching
       ├─→ Check against visa requirements
       └─→ Create validation check
   ↓
6. Update Document Status
   ├─→ 'verified' if all checks pass
   ├─→ 'rejected' if critical checks fail
   └─→ 'needs_attention' if warnings/pending
```

## Step-by-Step Details

### Step 1: File Upload

**Endpoint**: `POST /api/v1/case-documents/`

**Request** (multipart/form-data):
```
case_id: <uuid>
document_type_id: <uuid> (optional, can be auto-detected)
file: <binary file>
```

**What Happens**:
1. File validated (size, type, MIME type)
2. File stored using `FileStorageService` (local or S3)
3. `CaseDocument` record created with status `'uploaded'`
4. Signal `handle_document_uploaded` triggered
5. Celery task `process_document_task` queued

### Step 2: OCR Processing

**Service**: `OCRService`

**Supported Backends**:
- **Tesseract** (default) - Free, open-source
- **AWS Textract** - Cloud-based, high accuracy
- **Google Vision API** - Cloud-based, multi-language

**Configuration** (in `settings.py`):
```python
OCR_BACKEND = 'tesseract'  # or 'aws_textract' or 'google_vision'
```

**What Happens**:
1. Document file retrieved (from local storage or S3)
2. Text extracted using configured OCR backend
3. Extracted text stored in `CaseDocument.ocr_text` field
4. OCR metadata stored (confidence, page count, etc.)
5. `DocumentCheck` created:
   - `check_type = 'ocr'`
   - `result = 'passed'` if successful, `'failed'` if failed
   - `details = {metadata, error}`

**Edge Cases**:
- OCR fails → Check marked as `'failed'`, user can retry
- Low confidence → Check marked as `'warning'`
- Image-only document → OCR marked as `'pending'`, proceed with classification

### Step 3: Document Classification

**Service**: `DocumentClassificationService`

**Method**: Uses LLM (OpenAI GPT-4o-mini) to analyze:
- OCR extracted text
- File name
- File metadata

**What Happens**:
1. LLM analyzes OCR text and metadata
2. Predicts document type from available `DocumentType` codes
3. Returns confidence score (0.0 to 1.0)
4. If confidence >= 0.7:
   - Auto-updates `CaseDocument.document_type_id`
   - Stores `classification_confidence`
   - Check marked as `'passed'`
5. If confidence < 0.7:
   - Keeps original `document_type_id` (or null)
   - Check marked as `'warning'`
   - Flagged for human review
6. `DocumentCheck` created:
   - `check_type = 'classification'`
   - `result = 'passed'` or `'warning'` or `'failed'`
   - `details = {confidence, reasoning, metadata}`

**Example Classification**:
```json
{
  "document_type": "passport",
  "confidence": 0.95,
  "reasoning": "Document contains passport number, photo, and personal details"
}
```

### Step 4: Requirement Matching

**Status**: Placeholder (to be implemented)

**Future Implementation**:
- Load `visa_document_requirements` for case's visa type
- Check if uploaded document matches required document type
- Create validation check

### Step 5: Status Update

**Status Calculation**:
- `'verified'`: All critical checks passed (OCR + Classification)
- `'rejected'`: Any critical check failed
- `'needs_attention'`: Warnings or pending checks
- `'processing'`: Currently being processed

## API Response Example

**After Upload**:
```json
{
  "success": true,
  "message": "Case document created successfully.",
  "data": {
    "id": "...",
    "case_id": "...",
    "file_name": "passport.pdf",
    "status": "uploaded",
    "uploaded_at": "2024-01-15T11:00:00Z"
  }
}
```

**After Processing** (GET document):
```json
{
  "id": "...",
  "case_id": "...",
  "document_type_code": "passport",
  "file_name": "passport.pdf",
  "status": "verified",
  "ocr_text": "PASSPORT\nUNITED KINGDOM OF GREAT BRITAIN...",
  "classification_confidence": 0.95,
  "checks_count": 3,
  "file_url": "https://...",
  "uploaded_at": "2024-01-15T11:00:00Z"
}
```

## Services Created

### 1. OCRService (`src/document_handling/services/ocr_service.py`)

**Methods**:
- `extract_text(file_path, mime_type)` - Extract text from document
- `_extract_with_tesseract()` - Tesseract implementation
- `_extract_with_textract()` - AWS Textract implementation
- `_extract_with_google_vision()` - Google Vision implementation

**Features**:
- Multiple backend support
- Automatic backend selection
- Handles PDF and images
- Returns metadata (confidence, pages, etc.)

### 2. DocumentClassificationService (`src/document_handling/services/document_classification_service.py`)

**Methods**:
- `classify_document(ocr_text, file_name, file_size, mime_type)` - Classify document type
- `_classify_with_llm()` - LLM-based classification
- `should_auto_classify(confidence)` - Check if auto-classification should happen

**Features**:
- LLM-based classification (OpenAI GPT-4o-mini)
- Confidence scoring
- Auto-classification threshold (0.7)
- Human review flagging for low confidence

## Configuration

### OCR Backend

**Tesseract** (Default):
```python
# settings.py
OCR_BACKEND = 'tesseract'

# Install dependencies
pip install pytesseract pdf2image pillow
```

**AWS Textract**:
```python
# settings.py
OCR_BACKEND = 'aws_textract'
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_REGION = env('AWS_REGION', default='us-east-1')
```

**Google Vision**:
```python
# settings.py
OCR_BACKEND = 'google_vision'
GOOGLE_APPLICATION_CREDENTIALS = env('GOOGLE_APPLICATION_CREDENTIALS')  # Path to JSON key
```

### Classification

**OpenAI** (Required):
```python
# settings.py
OPENAI_API_KEY = env('OPENAI_API_KEY')
```

## Database Schema

### CaseDocument Model

**New Fields Added**:
- `ocr_text` (TextField) - Extracted text from OCR
- `classification_confidence` (FloatField) - Confidence score (0.0 to 1.0)

**Existing Fields**:
- `document_type` (ForeignKey) - Can be auto-updated by classification
- `status` - Updated based on check results

### DocumentCheck Model

**Check Types**:
- `'ocr'` - OCR extraction result
- `'classification'` - Document type classification
- `'validation'` - Requirement matching (future)

**Results**:
- `'passed'` - Check successful
- `'failed'` - Check failed
- `'warning'` - Check passed but needs attention
- `'pending'` - Check not yet performed

## Error Handling

### OCR Failures
- If OCR fails → Check marked as `'failed'`
- Document status → `'needs_attention'`
- User can retry upload
- Error details stored in check `details`

### Classification Failures
- If classification fails → Check marked as `'failed'`
- Document type not auto-updated
- Requires manual classification
- Error details stored in check `details`

### Low Confidence Classification
- If confidence < 0.7 → Check marked as `'warning'`
- Document type not auto-updated
- Flagged for human review
- User can manually select document type

## Testing

### Test OCR
```python
from document_handling.services.ocr_service import OCRService

text, metadata, error = OCRService.extract_text(
    file_path='case_documents/.../document.pdf',
    mime_type='application/pdf'
)
print(f"Extracted {len(text)} characters")
```

### Test Classification
```python
from document_handling.services.document_classification_service import DocumentClassificationService

doc_type_id, confidence, metadata, error = DocumentClassificationService.classify_document(
    ocr_text="PASSPORT\nUNITED KINGDOM...",
    file_name="passport.pdf"
)
print(f"Classified as {doc_type_id} with confidence {confidence}")
```

## Files Created/Modified

### Created:
- `src/document_handling/services/ocr_service.py`
- `src/document_handling/services/document_classification_service.py`
- `src/document_handling/migrations/0001_add_ocr_and_classification_fields.py`

### Modified:
- `src/document_handling/models/case_document.py` - Added `ocr_text` and `classification_confidence`
- `src/document_handling/tasks/document_tasks.py` - Implemented actual OCR and classification
- `src/document_handling/services/case_document_service.py` - Handle document_type_id updates
- `src/document_handling/serializers/case_document/read.py` - Include OCR and classification fields

## Next Steps

1. ✅ **OCR Service** - Implemented (supports Tesseract, AWS Textract, Google Vision)
2. ✅ **Classification Service** - Implemented (LLM-based)
3. ✅ **Document Processing Task** - Fully implemented
4. ⏳ **Requirement Matching** - Placeholder (to be implemented)
5. ⏳ **Content Validation** - Future enhancement (validate against case facts)

## Dependencies

**For Tesseract**:
```bash
pip install pytesseract pdf2image pillow
# Also need Tesseract installed on system
```

**For AWS Textract**:
```bash
pip install boto3
```

**For Google Vision**:
```bash
pip install google-cloud-vision
```

**For Classification**:
```bash
pip install openai
```

## Notes

- OCR text is stored in database for search and analysis
- Classification confidence threshold is 0.7 (configurable)
- Low confidence classifications require human review
- Document type can be manually overridden by user/reviewer
- All processing is asynchronous via Celery
- Processing status is tracked in real-time

