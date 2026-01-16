# Document Classification Helpers

This document describes the helper files created for document classification, which organize prompts, document type descriptions, and classification guidelines into separate, maintainable modules.

## Directory Structure

```
src/document_handling/helpers/
├── __init__.py                          # Exports all helper functions
├── prompts.py                            # LLM prompt templates
├── document_type_descriptions.py        # Document type descriptions and indicators
└── classification_guidelines.py         # Classification rules and guidelines
```

## Files Overview

### 1. `prompts.py`
Contains prompt templates and system messages for LLM-based document classification.

**Key Functions:**
- `build_document_classification_prompt()`: Builds comprehensive classification prompt
- `get_system_message()`: Returns system message for LLM
- `_get_document_type_descriptions_with_fallback()`: Gets document type descriptions (database first, then fallback)

**Usage:**
```python
from document_handling.helpers.prompts import build_document_classification_prompt, get_system_message

prompt = build_document_classification_prompt(
    ocr_text="...",
    file_name="passport.pdf",
    possible_types=['PASSPORT', 'BANK_STATEMENT']
)
```

### 2. `document_type_descriptions.py`
Contains detailed descriptions and key indicators for different document types.

**Key Components:**
- `DOCUMENT_TYPE_DESCRIPTIONS`: Dictionary with descriptions and indicators for 18+ document types
- `get_document_type_description()`: Get description for a specific document type
- `format_document_types_for_prompt()`: Format document types for LLM prompt

**Supported Document Types:**
- PASSPORT
- BIRTH_CERTIFICATE
- BANK_STATEMENT
- CERTIFICATE_OF_SPONSORSHIP
- EDUCATION_CERTIFICATE
- LANGUAGE_TEST
- MARRIAGE_CERTIFICATE
- EMPLOYMENT_LETTER
- ACCOMMODATION_EVIDENCE
- CRIMINAL_RECORD_CHECK
- FINANCIAL_EVIDENCE
- TRAVEL_HISTORY
- MEDICAL_CERTIFICATE
- PHOTO_ID
- PROOF_OF_ADDRESS
- VISA_STAMP
- SPONSOR_LETTER
- DEPENDANT_DOCUMENTS

**Usage:**
```python
from document_handling.helpers.document_type_descriptions import get_document_type_description

doc_info = get_document_type_description('PASSPORT')
# Returns: {'description': '...', 'key_indicators': [...]}
```

### 3. `classification_guidelines.py`
Contains classification rules, confidence scoring guidelines, and edge case handling instructions.

**Key Components:**
- `CLASSIFICATION_GUIDELINES`: Dictionary with guideline sections
- `COMMON_DOCUMENT_INDICATORS`: Detailed indicators for common document types
- `get_classification_guidelines()`: Get formatted guidelines
- `get_common_document_indicators()`: Get all common document indicators
- `get_document_indicators_for_types()`: Get indicators for specific document types

**Guideline Sections:**
1. **Key Indicators to Look For**: What to search for in documents
2. **Confidence Scoring**: How to assign confidence scores (0.0-1.0)
3. **Edge Cases to Handle**: How to handle ambiguous, partial, or multi-document files
4. **Classification Rules**: General rules for classification

**Usage:**
```python
from document_handling.helpers.classification_guidelines import get_classification_guidelines

guidelines = get_classification_guidelines()
```

## Benefits of This Structure

1. **Separation of Concerns**: Prompts, descriptions, and guidelines are in separate files
2. **Maintainability**: Easy to update prompts or add new document types
3. **Reusability**: Helper functions can be used across different services
4. **Testability**: Each helper can be tested independently
5. **Readability**: Code is cleaner and easier to understand

## Integration with Services

The `DocumentClassificationService` now uses these helpers:

```python
from document_handling.helpers.prompts import build_document_classification_prompt, get_system_message

# In _classify_with_llm method:
prompt = build_document_classification_prompt(
    ocr_text=ocr_text,
    file_name=file_name,
    possible_types=possible_types
)

response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "system", "content": get_system_message()},
        {"role": "user", "content": prompt}
    ],
    ...
)
```

## Adding New Document Types

To add a new document type:

1. **Add to `document_type_descriptions.py`:**
```python
DOCUMENT_TYPE_DESCRIPTIONS['NEW_DOCUMENT_TYPE'] = {
    'description': 'Description of the document type',
    'key_indicators': [
        'Indicator 1',
        'Indicator 2',
        ...
    ]
}
```

2. **Add to `classification_guidelines.py` (if needed):**
```python
COMMON_DOCUMENT_INDICATORS['NEW_DOCUMENT_TYPE'] = """   **NEW_DOCUMENT_TYPE**:
   - Indicator 1
   - Indicator 2
   ..."""
```

3. **Ensure it's in the database** (via Django admin or migration)

## Future Enhancements

- Add support for jurisdiction-specific document types
- Add multilingual document type descriptions
- Create prompt templates for other LLM tasks (e.g., document validation)
- Add prompt versioning for A/B testing
- Create prompt templates for different LLM models (GPT-4, Claude, etc.)

