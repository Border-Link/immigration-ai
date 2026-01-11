# UK Ingestion Storage Flow

## Architecture Overview

The UK ingestion system follows a **separation of concerns** pattern:

- **`uk_ingestion.py`**: Only fetches and parses data (NO database storage)
- **`IngestionService`**: Orchestrates the flow and stores data to database

## Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Entry Point                                               │
│    IngestionService.ingest_data_source(data_source_id)      │
│    OR                                                         │
│    ingest_uk_sources_weekly_task (Celery Beat)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Create UK Ingestion System                                │
│    IngestionSystemFactory.create(data_source)               │
│    → Returns: UKIngestionSystem instance                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Discover URLs (uk_ingestion.py)                          │
│    ingestion_system.get_document_urls()                     │
│    → Uses Content API to find taxons                         │
│    → Uses Search API to find content pages                   │
│    → Returns: List of URLs                                   │
│    ❌ NO DATABASE STORAGE HERE                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Process Each URL (IngestionService._process_url)          │
│    For each URL in the list:                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Fetch Content (uk_ingestion.py)                           │
│    ingestion_system.fetch_content(url)                      │
│    → Makes HTTP GET request                                  │
│    → Returns: {'content': '...', 'content_type': '...'}      │
│    ❌ NO DATABASE STORAGE HERE                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. ✅ STORE SourceDocument (IngestionService line 117)      │
│    SourceDocumentRepository.create_source_document(          │
│        data_source=data_source,                              │
│        source_url=url,                                       │
│        raw_content=fetch_result['content'],  ← FULL JSON    │
│        content_type=fetch_result['content_type'],            │
│        http_status_code=fetch_result['status_code']          │
│    )                                                         │
│    → Creates record in 'source_documents' table              │
│    → Stores FULL JSON in raw_content field                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Extract Text (uk_ingestion.py)                           │
│    ingestion_system.extract_text(raw_content)               │
│    → Extracts key fields for hashing                         │
│    → Returns: Extracted text string                          │
│    ❌ NO DATABASE STORAGE HERE                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Extract Metadata (uk_ingestion.py)                        │
│    ingestion_system.extract_metadata(raw_content)           │
│    → Extracts structured metadata                            │
│    → Returns: Metadata dict                                  │
│    ❌ NO DATABASE STORAGE HERE                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. ✅ STORE DocumentVersion (IngestionService line 149)     │
│    DocumentVersionRepository.create_document_version(        │
│        source_document=source_doc,                            │
│        raw_text=extracted_text,  ← Extracted text            │
│        metadata=metadata  ← Structured metadata              │
│    )                                                         │
│    → Creates record in 'document_versions' table             │
│    → Stores SHA-256 hash in content_hash                     │
│    → Stores extracted text in raw_text                       │
│    → Stores metadata in metadata JSONField                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. ✅ STORE DocumentDiff (if changed, line 170)            │
│     DocumentDiffRepository.create_document_diff(            │
│         old_version=previous_version,                        │
│         new_version=new_version,                             │
│         diff_text=diff_text,                                 │
│         change_type=change_type                              │
│     )                                                        │
│     → Creates record in 'document_diffs' table              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. ✅ STORE ParsedRule (via RuleParsingService, line 184)  │
│     RuleParsingService.parse_document_version(new_version)  │
│     → Creates records in 'parsed_rules' table                │
│     → Stores extracted rules, JSON Logic, confidence         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 12. ✅ STORE RuleValidationTask (line 186)                  │
│     → Creates records in 'rule_validation_tasks' table       │
│     → Links to ParsedRule for human review                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Points

### ❌ UK Ingestion System Does NOT Store Data
- `uk_ingestion.py` only:
  - Fetches data from APIs
  - Parses JSON responses
  - Extracts text and metadata
  - Returns data structures

### ✅ IngestionService Stores Data
- `IngestionService._process_url()` is where ALL database storage happens:
  - Line 117: Stores `SourceDocument` (full JSON)
  - Line 149: Stores `DocumentVersion` (extracted text + metadata)
  - Line 170: Stores `DocumentDiff` (if content changed)
  - Line 184: Triggers rule parsing which stores `ParsedRule`
  - Line 186: Stores `RuleValidationTask`

## File Locations

### Data Fetching (No DB Storage)
- **File**: `src/data_ingestion/ingestion/uk_ingestion.py`
- **Methods**: 
  - `fetch_content()` - Fetches from API
  - `extract_text()` - Extracts text
  - `extract_metadata()` - Extracts metadata
  - `get_document_urls()` - Discovers URLs

### Data Storage (Database Operations)
- **File**: `src/data_ingestion/services/ingestion_service.py`
- **Method**: `_process_url()` - Lines 92-189
- **Repositories Used**:
  - `SourceDocumentRepository` (line 117)
  - `DocumentVersionRepository` (line 149)
  - `DocumentDiffRepository` (line 170)
  - `RuleParsingService` (line 184) → Creates ParsedRule

## Database Tables Populated

1. **`source_documents`** - Full JSON from API
2. **`document_versions`** - Extracted text + metadata
3. **`document_diffs`** - Change tracking
4. **`parsed_rules`** - AI-extracted rules
5. **`rule_validation_tasks`** - Review tasks

## Summary

The UK ingestion system is a **data fetcher/parser**, not a data storer. All database storage happens in `IngestionService._process_url()` which:
1. Calls UK ingestion methods to fetch/parse
2. Stores results using repositories
3. Triggers rule parsing
4. Creates validation tasks

This separation allows the UK ingestion system to be jurisdiction-specific (fetching logic) while keeping storage logic generic and reusable.

