# Document Upload Implementation Summary

## Overview

Document upload functionality has been fully implemented for case files. Users can upload documents (PDF, images, Word docs) which are stored securely and processed through OCR and validation.

## What Was Implemented

### 1. ✅ File Storage Service
**Location**: `src/document_handling/services/file_storage_service.py`

**Features**:
- ✅ File validation (size, type, MIME type)
- ✅ Local filesystem storage
- ✅ S3 storage support (AWS S3 or DigitalOcean Spaces)
- ✅ File path generation with UUID-based naming
- ✅ File URL generation (presigned URLs for S3)
- ✅ File deletion

**Configuration**:
- Uses `USE_S3_STORAGE` setting to switch between local and S3
- Supports both AWS S3 and DigitalOcean Spaces (via endpoint URL)

### 2. ✅ Updated Document Upload API
**Location**: `src/document_handling/views/case_document/create.py`

**Changes**:
- ✅ Now handles actual file uploads (multipart/form-data)
- ✅ Validates and stores files using FileStorageService
- ✅ Creates CaseDocument record with file metadata
- ✅ Automatic cleanup on failure

### 3. ✅ Updated Serializer
**Location**: `src/document_handling/serializers/case_document/create.py`

**Changes**:
- ✅ Accepts `file` field (FileField) instead of just metadata
- ✅ Auto-detects file_name, file_size, mime_type from uploaded file
- ✅ Validates file using FileStorageService

### 4. ✅ Enhanced Document Service
**Location**: `src/document_handling/services/case_document_service.py`

**New Methods**:
- ✅ `get_file_url()` - Get URL to access/download file
- ✅ `delete_case_document()` - Now also deletes stored file

### 5. ✅ Enhanced Serializer (Read)
**Location**: `src/document_handling/serializers/case_document/read.py`

**Changes**:
- ✅ Added `file_url` field to serializer response
- ✅ Automatically generates file access URL

## File Storage Configuration

### Local Storage (Default)

Add to `settings.py`:
```python
# Media files (uploaded documents)
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
```

Files are stored in: `media/case_documents/{case_id}/{document_type_id}/{uuid}.{ext}`

### S3 Storage (Optional)

Add to `settings.py`:
```python
# S3 Storage Configuration
USE_S3_STORAGE = True
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')

# For DigitalOcean Spaces (optional)
AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL', default=None)
```

Add to `.env`:
```bash
USE_S3_STORAGE=True
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
# For DigitalOcean Spaces:
# AWS_S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
```

## API Usage

### Upload Document

**Endpoint**: `POST /api/v1/case-documents/`

**Request** (multipart/form-data):
```
case_id: <uuid>
document_type_id: <uuid>
file: <binary file>
```

**Response**:
```json
{
  "success": true,
  "message": "Case document created successfully.",
  "data": {
    "id": "...",
    "case_id": "...",
    "file_name": "passport.pdf",
    "file_size": 123456,
    "mime_type": "application/pdf",
    "status": "uploaded",
    "file_url": "https://...",
    "uploaded_at": "2024-..."
  }
}
```

### Get Document

**Endpoint**: `GET /api/v1/case-documents/{id}/`

**Response** includes `file_url` for downloading/viewing the file.

### Delete Document

**Endpoint**: `DELETE /api/v1/case-documents/{id}/`

Deletes both the database record and the stored file.

## File Validation

### Allowed File Types
- PDF (`.pdf`)
- Images (`.jpg`, `.jpeg`, `.png`)
- Word Documents (`.doc`, `.docx`)

### File Size Limit
- Maximum: **10MB**

### Validation Checks
1. File size validation
2. File extension validation
3. MIME type validation
4. File existence check

## File Processing Flow

```
1. User uploads file via API
   ↓
2. FileStorageService validates file
   ↓
3. File stored (local or S3)
   ↓
4. CaseDocument record created
   ↓
5. Signal triggers async processing
   ↓
6. OCR, classification, validation (Celery task)
   ↓
7. Document status updated
```

## Security Features

- ✅ File type validation
- ✅ File size limits
- ✅ UUID-based file naming (prevents conflicts)
- ✅ Private file storage (S3 ACL: private)
- ✅ Presigned URLs for S3 (expire in 1 hour)
- ✅ File cleanup on deletion

## Error Handling

- ✅ Validation errors returned to client
- ✅ File storage errors logged
- ✅ Automatic cleanup if document creation fails
- ✅ Graceful fallback if S3 not configured

## Next Steps

1. ✅ **File upload implemented** - Complete
2. ⏳ **Add MEDIA_ROOT and MEDIA_URL to settings** (if using local storage)
3. ⏳ **Configure S3 credentials** (if using S3 storage)
4. ⏳ **Implement actual OCR service** (currently placeholder)
5. ⏳ **Implement document classification** (currently placeholder)
6. ⏳ **Add file download endpoint** (optional, file_url already provided)

## Files Created/Modified

### Created:
- `src/document_handling/services/file_storage_service.py`

### Modified:
- `src/document_handling/views/case_document/create.py`
- `src/document_handling/serializers/case_document/create.py`
- `src/document_handling/serializers/case_document/read.py`
- `src/document_handling/services/case_document_service.py`

## Testing

### Test File Upload
```python
import requests

url = "http://localhost:8000/api/v1/case-documents/"
files = {'file': open('passport.pdf', 'rb')}
data = {
    'case_id': '...',
    'document_type_id': '...'
}
response = requests.post(url, files=files, data=data, headers={'Authorization': 'Bearer ...'})
print(response.json())
```

### Test File Download
```python
# Get document
response = requests.get(f"http://localhost:8000/api/v1/case-documents/{document_id}/")
file_url = response.json()['data']['file_url']

# Download file
file_response = requests.get(file_url)
with open('downloaded.pdf', 'wb') as f:
    f.write(file_response.content)
```

## Notes

- Files are stored with UUID-based names to prevent conflicts
- File paths are organized by case_id and document_type_id
- S3 presigned URLs expire after 1 hour (configurable)
- Local storage creates directories automatically
- File deletion is automatic when document is deleted

