# Document Upload - How It Works

## Complete Flow Explanation

### 1. User Uploads Document

**What User Does**:
```bash
POST /api/v1/case-documents/
Content-Type: multipart/form-data

case_id: <uuid>
document_type_id: <uuid> (optional - can be auto-detected)
file: <binary file>
```

**What Happens Behind the Scenes**:
1. **File Validation** (`FileStorageService.validate_file()`)
   - Checks file size (max 10MB)
   - Validates file type (PDF, images, Word docs)
   - Validates MIME type

2. **File Storage** (`FileStorageService.store_file()`)
   - Generates unique file path: `case_documents/{case_id}/{document_type_id}/{uuid}.{ext}`
   - Stores file (local filesystem or S3)
   - Returns file path

3. **Database Record** (`CaseDocumentService.create_case_document()`)
   - Creates `CaseDocument` record
   - Status: `'uploaded'`
   - Links to case and document type

4. **Signal Triggered** (`handle_document_uploaded`)
   - Queues Celery task: `process_document_task.delay(document_id)`
   - Sends notification to user

---

### 2. Async Processing Starts

**Celery Task**: `process_document_task(document_id)`

**Status Update**: `'uploaded'` → `'processing'`

---

### 3. OCR Extraction

**Service**: `OCRService.extract_text()`

**What It Does**:
1. Retrieves document file (from local storage or S3)
2. Extracts text using configured OCR backend:
   - **Tesseract**: Free, open-source (default)
   - **AWS Textract**: Cloud-based, high accuracy
   - **Google Vision**: Cloud-based, multi-language
3. Returns extracted text, metadata, and any errors

**Result Storage**:
- Extracted text → `CaseDocument.ocr_text` field
- OCR metadata → `DocumentCheck.details` (confidence, pages, etc.)

**Check Created**:
```python
DocumentCheck(
    check_type='ocr',
    result='passed' or 'failed',
    details={'metadata': {...}, 'error': '...'},
    performed_by='OCR Service'
)
```

**Edge Cases**:
- ✅ **OCR succeeds** → Text stored, check = `'passed'`
- ❌ **OCR fails** → Check = `'failed'`, error stored
- ⚠️ **Low confidence** → Check = `'warning'`
- ⏸️ **Image-only** → Check = `'pending'`, proceed anyway

---

### 4. Document Classification

**Service**: `DocumentClassificationService.classify_document()`

**What It Does**:
1. Takes OCR text + file metadata
2. Calls LLM (OpenAI GPT-4o-mini) with prompt:
   ```
   "Analyze this document and classify it as one of: passport, bank_statement, etc."
   ```
3. LLM returns:
   ```json
   {
     "document_type": "passport",
     "confidence": 0.95,
     "reasoning": "Contains passport number, photo, personal details"
   }
   ```
4. Validates document type exists in database
5. Returns document_type_id, confidence, metadata

**Auto-Classification Logic**:
- **If confidence >= 0.7**:
  - ✅ Auto-updates `CaseDocument.document_type_id`
  - ✅ Stores `CaseDocument.classification_confidence`
  - ✅ Check = `'passed'`
  
- **If confidence < 0.7**:
  - ⚠️ Does NOT auto-update document_type_id
  - ⚠️ Check = `'warning'`
  - ⚠️ Flagged for human review
  - User can manually select document type

**Check Created**:
```python
DocumentCheck(
    check_type='classification',
    result='passed' or 'warning' or 'failed',
    details={
        'confidence': 0.95,
        'reasoning': '...',
        'metadata': {...}
    },
    performed_by='AI Classification Service'
)
```

---

### 5. Requirement Matching

**Status**: Placeholder (to be implemented)

**Future Implementation**:
- Load visa document requirements for case's visa type
- Check if uploaded document matches required type
- Create validation check

---

### 6. Status Update

**Status Calculation**:
```python
if any_check_failed:
    status = 'rejected'
elif all_critical_checks_passed:
    status = 'verified'
else:
    status = 'needs_attention'
```

**Status Meanings**:
- `'uploaded'` - Just uploaded, waiting for processing
- `'processing'` - Currently being processed (OCR/classification)
- `'verified'` - All checks passed, document is valid
- `'rejected'` - Critical check failed, document invalid
- `'needs_attention'` - Warnings or pending checks, needs review

---

## Example: Complete Flow

### User Uploads Passport

1. **Upload**:
   ```
   POST /api/v1/case-documents/
   file: passport.pdf
   ```

2. **File Stored**:
   ```
   Path: case_documents/{case_id}/{doc_type_id}/abc123.pdf
   Status: 'uploaded'
   ```

3. **OCR Processing** (async):
   ```
   OCRService.extract_text() → 
   Text: "PASSPORT\nUNITED KINGDOM OF GREAT BRITAIN...\nPassport No: 123456789..."
   Stored in: CaseDocument.ocr_text
   Check: {type: 'ocr', result: 'passed'}
   ```

4. **Classification** (async):
   ```
   DocumentClassificationService.classify_document() →
   LLM analyzes: "PASSPORT\nUNITED KINGDOM...\nPassport No..."
   Returns: {document_type: 'passport', confidence: 0.95}
   
   Confidence 0.95 >= 0.7 → Auto-update document_type_id
   Stored: CaseDocument.classification_confidence = 0.95
   Check: {type: 'classification', result: 'passed', confidence: 0.95}
   ```

5. **Status Update**:
   ```
   OCR: passed ✅
   Classification: passed ✅
   → Status: 'verified'
   ```

6. **User Gets Response**:
   ```json
   {
     "id": "...",
     "file_name": "passport.pdf",
     "status": "verified",
     "document_type_code": "passport",
     "classification_confidence": 0.95,
     "ocr_text": "PASSPORT\nUNITED KINGDOM...",
     "checks_count": 2
   }
   ```

---

## Configuration

### OCR Backend

**Default (Tesseract)**:
```python
# settings.py
OCR_BACKEND = 'tesseract'

# Install
pip install pytesseract pdf2image pillow
# Also install Tesseract on system
```

**AWS Textract**:
```python
OCR_BACKEND = 'aws_textract'
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
```

**Google Vision**:
```python
OCR_BACKEND = 'google_vision'
GOOGLE_APPLICATION_CREDENTIALS = env('GOOGLE_APPLICATION_CREDENTIALS')
```

### Classification

**OpenAI** (Required):
```python
OPENAI_API_KEY = env('OPENAI_API_KEY')
```

---

## Key Features

### ✅ Automatic Document Reading
- OCR extracts all text from documents
- Supports PDF, images, Word docs
- Multiple OCR backends supported

### ✅ Intelligent Categorization
- LLM analyzes document content
- Predicts document type automatically
- High confidence → Auto-classifies
- Low confidence → Flags for review

### ✅ Content Storage
- OCR text stored in database
- Searchable and analyzable
- Can be used for content validation (future)

### ✅ Status Tracking
- Real-time status updates
- Detailed check results
- User notifications

### ✅ Error Handling
- OCR failures don't block classification
- Low confidence classifications flagged
- User can retry or manually classify

---

## API Endpoints

### Upload Document
```
POST /api/v1/case-documents/
Content-Type: multipart/form-data

case_id: <uuid>
document_type_id: <uuid> (optional)
file: <binary>
```

### Get Document Status
```
GET /api/v1/case-documents/{id}/

Response includes:
- status (uploaded/processing/verified/rejected)
- ocr_text (extracted text)
- classification_confidence
- checks (all check results)
```

### Get Document Checks
```
GET /api/v1/case-documents/{id}/checks/

Returns all checks (OCR, classification, validation)
```

---

## Database Fields

### CaseDocument
- `ocr_text` - Full extracted text from OCR
- `classification_confidence` - Confidence score (0.0 to 1.0)
- `document_type` - Can be auto-updated by classification
- `status` - Current processing status

### DocumentCheck
- `check_type` - 'ocr', 'classification', 'validation'
- `result` - 'passed', 'failed', 'warning', 'pending'
- `details` - JSON with metadata, confidence, errors
- `performed_by` - 'OCR Service', 'AI Classification Service', etc.

---

## Summary

**The system now**:
1. ✅ **Stores files** securely (local or S3)
2. ✅ **Reads documents** using OCR (extracts all text)
3. ✅ **Categorizes documents** using AI (predicts document type)
4. ✅ **Stores content** in database (OCR text searchable)
5. ✅ **Tracks status** throughout processing
6. ✅ **Handles errors** gracefully
7. ✅ **Flags for review** when confidence is low

**Everything works automatically** - user uploads, system reads, categorizes, and stores everything!

