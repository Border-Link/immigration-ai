"""
Document Handling Prompts

Contains comprehensive prompt templates for all LLM-based document processing operations:
- Document classification
- Expiry date extraction
- Content validation
"""

from document_handling.helpers.document_type_descriptions import get_document_type_description
from document_handling.helpers.classification_guidelines import (
    get_classification_guidelines,
    get_common_document_indicators,
    get_document_indicators_for_types
)
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector


def build_document_classification_prompt(
    ocr_text: str,
    file_name: str = None,
    possible_types: list = None
) -> str:
    """
    Build comprehensive prompt for document classification.
    
    Args:
        ocr_text: Extracted text from OCR
        file_name: Original file name
        possible_types: List of possible document type codes
        
    Returns:
        Complete formatted prompt string
    """
    # Get document type descriptions (try database first, then fallback)
    document_type_descriptions = _get_document_type_descriptions_with_fallback(possible_types)
    
    # Get classification guidelines
    guidelines = get_classification_guidelines()
    
    # Get document indicators for available types
    document_indicators = get_document_indicators_for_types(possible_types)
    
    # Build prompt
    prompt = f"""You are an expert document classification system for immigration visa applications. 
Your task is to accurately classify documents based on their content, structure, and key indicators.

## Available Document Types:
{document_type_descriptions}

## Document Information:
- Filename: {file_name or 'unknown'}
- Extracted Text (first 3000 characters):
{ocr_text[:3000]}

## Classification Guidelines:

{guidelines}

4. **Common Document Type Indicators**:

{document_indicators if document_indicators else get_common_document_indicators()}

## Your Task:
Analyze the document and classify it. Respond with ONLY valid JSON in this exact format:
{{
  "document_type": "passport",
  "confidence": 0.95,
  "reasoning": "Document contains passport number, photo page, issuing authority 'HM Passport Office', nationality 'British', and expiry date. Clear passport indicators present."
}}

**Important**: 
- The "document_type" MUST be one of the available types listed above (case-sensitive)
- Confidence must be between 0.0 and 1.0
- Provide detailed reasoning explaining which indicators led to the classification
- Only respond with valid JSON, no markdown, no additional text"""

    return prompt


def _get_document_type_descriptions_with_fallback(possible_types: list) -> str:
    """
    Get document type descriptions, trying database first, then falling back to defaults.
    
    Args:
        possible_types: List of document type codes
        
    Returns:
        Formatted string with document type descriptions
    """
    if not possible_types:
        return "No document types available."
    
    type_list = []
    for doc_type_code in possible_types:
        # Try to get from database first
        try:
            doc_type = DocumentTypeSelector.get_by_code(doc_type_code)
            description = doc_type.description or doc_type.name
            type_list.append(f"- **{doc_type_code}**: {description}")
        except:
            # Fall back to default descriptions
            doc_info = get_document_type_description(doc_type_code)
            description = doc_info['description']
            type_list.append(f"- **{doc_type_code}**: {description}")
    
    return '\n'.join(type_list) if type_list else "No document types available."


def get_classification_system_message() -> str:
    """
    Get system message for LLM classification.
    
    Returns:
        System message string
    """
    return (
        "You are a precise document classification assistant for immigration visa applications. "
        "You analyze documents and classify them into specific types. "
        "Always respond with valid JSON only, no markdown formatting, no additional text."
    )


def build_expiry_date_extraction_prompt(
    ocr_text: str,
    document_type_code: str = None,
    file_name: str = None
) -> str:
    """
    Build comprehensive prompt for expiry date extraction.
    
    Args:
        ocr_text: Extracted text from OCR
        document_type_code: Document type code (e.g., 'passport', 'visa')
        file_name: Original file name
        
    Returns:
        Complete formatted prompt string
    """
    # Document type specific guidance
    document_type_guidance = _get_expiry_extraction_guidance(document_type_code)
    
    prompt = f"""You are an expert document analysis system for immigration visa applications.
Your task is to accurately extract expiry dates from documents with high precision.

## Document Information:
- Document Type: {document_type_code or 'Unknown'}
- File Name: {file_name or 'Unknown'}
- Extracted Text (first 2000 characters):
{ocr_text[:2000]}

## Expiry Date Extraction Guidelines:

{document_type_guidance}

## Common Date Formats to Look For:
1. **ISO Format**: YYYY-MM-DD (e.g., 2025-12-31)
2. **UK Format**: DD/MM/YYYY (e.g., 31/12/2025)
3. **US Format**: MM/DD/YYYY (e.g., 12/31/2025)
4. **Written Format**: DD Month YYYY (e.g., 31 December 2025)
5. **Short Format**: DD-MM-YY (e.g., 31-12-25) - be careful with century interpretation

## Key Indicators to Search For:
- "Date of Expiry", "Expiry Date", "Expires", "Valid Until", "Valid To"
- "Date d'expiration" (French), "Fecha de expiración" (Spanish)
- "Expiration Date", "Expiration", "Expiry"
- "Valid Until", "Valid To", "Valid Thru"
- "Expires On", "Expiry On", "Expires Date"

## Important Considerations:
1. **Multiple Dates**: If multiple dates are found, prioritize:
   - Dates explicitly labeled as "expiry", "expiration", "valid until"
   - Dates in the future (not past dates)
   - Dates that match the document type context
   
2. **Date Validation**:
   - Ensure the date is in the future (or very recent past for recently expired documents)
   - Check for logical consistency (e.g., expiry date should be after issue date)
   - Be cautious with ambiguous formats (DD/MM vs MM/DD)
   
3. **Confidence Scoring**:
   - High confidence (0.9-1.0): Clear expiry date label, unambiguous format, future date
   - Medium confidence (0.7-0.9): Date found but format ambiguous or label unclear
   - Low confidence (0.5-0.7): Possible expiry date but uncertain
   - Very low confidence (<0.5): Unlikely to be expiry date

4. **Edge Cases**:
   - If no expiry date is found, return null for expiry_date
   - If document type doesn't typically have expiry dates, return null
   - If date format is completely unreadable, return null with low confidence

## Your Task:
Analyze the document text and extract the expiry date. Respond with ONLY valid JSON in this exact format:
{{
  "expiry_date": "YYYY-MM-DD" or null,
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of where the date was found, what format it was in, and why you're confident/uncertain",
  "extracted_text": "The exact text snippet containing the date",
  "date_format_detected": "ISO/UK/US/Written/Short",
  "alternative_dates_found": ["list of other dates found that might be relevant"]
}}

**Important**: 
- Always return dates in ISO format (YYYY-MM-DD)
- If no expiry date is found, set expiry_date to null
- Confidence must be between 0.0 and 1.0
- Provide detailed reasoning explaining your extraction process
- Include the exact text snippet where the date was found
- Only respond with valid JSON, no markdown, no additional text"""

    return prompt


def _get_expiry_extraction_guidance(document_type_code: str = None) -> str:
    """Get document type specific guidance for expiry date extraction."""
    guidance_map = {
        'passport': """**Passport Expiry Date Extraction**:
- Look for "Date of Expiry", "Expiry Date", or "Date d'expiration"
- Usually found on the photo/information page
- Format is typically DD/MM/YYYY or DD MMM YYYY
- May be labeled as "Valid Until" or "Expires"
- Passport expiry dates are typically 5-10 years from issue date""",
        
        'visa': """**Visa Expiry Date Extraction**:
- Look for "Valid Until", "Expiry Date", "Expires", or "Date of Expiry"
- May be labeled as "Valid To" or "Expiration Date"
- Format varies by country (check for DD/MM/YYYY, MM/DD/YYYY, or YYYY-MM-DD)
- Visa expiry dates are typically shorter (months to a few years)
- May be part of a date range (valid from/to)""",
        
        'certificate': """**Certificate Expiry Date Extraction**:
- Look for "Expires", "Valid Until", "Expiration Date"
- May be labeled as "Valid To" or "Expiry"
- Format varies by certificate type and issuing authority
- Some certificates may not have expiry dates (return null if not found)
- Check for renewal dates or validity periods""",
        
        'license': """**License Expiry Date Extraction**:
- Look for "Expiry Date", "Expires", "Valid Until", "Renewal Date"
- May be labeled as "Valid To" or "Expiration"
- Format typically DD/MM/YYYY or DD-MM-YYYY
- Licenses often have specific renewal periods
- Check for both expiry and renewal dates"""
    }
    
    if document_type_code and document_type_code.lower() in guidance_map:
        return guidance_map[document_type_code.lower()]
    
    return """**General Expiry Date Extraction**:
- Search for any date-related fields that indicate expiration
- Look for keywords: expiry, expiration, valid until, expires
- Check both labeled and unlabeled dates
- Prioritize dates in the future
- Consider document context when determining expiry dates"""


def get_expiry_extraction_system_message() -> str:
    """
    Get system message for expiry date extraction.
    
    Returns:
        System message string
    """
    return (
        "You are a precise document analysis expert for immigration visa applications. "
        "You extract expiry dates from documents with high accuracy. "
        "Always respond with valid JSON only, no markdown formatting, no additional text."
    )


def build_content_validation_prompt(
    ocr_text: str,
    case_facts: dict,
    document_type_code: str = None,
    extracted_metadata: dict = None
) -> str:
    """
    Build comprehensive prompt for content validation against case facts.
    
    Args:
        ocr_text: Extracted text from OCR
        case_facts: Dictionary of case facts (fact_key -> fact_value)
        document_type_code: Document type code
        extracted_metadata: Extracted metadata from document
        
    Returns:
        Complete formatted prompt string
    """
    # Format case facts for prompt
    facts_text = "\n".join([f"- **{key}**: {value}" for key, value in sorted(case_facts.items())])
    
    metadata_text = ""
    if extracted_metadata:
        import json
        metadata_text = f"""
## Extracted Document Metadata:
{json.dumps(extracted_metadata, indent=2)}"""
    
    # Document type specific validation guidance
    validation_guidance = _get_validation_guidance(document_type_code)
    
    prompt = f"""You are an expert document validation system for immigration visa applications.
Your task is to compare document content with case facts and identify matches, mismatches, and missing information.

## Document Information:
- Document Type: {document_type_code or 'Unknown'}
{metadata_text}

## Case Facts (Expected Information):
{facts_text}

## Document Text (Extracted Content):
{ocr_text[:2000]}

## Content Validation Guidelines:

{validation_guidance}

## Validation Process:

1. **Name Matching**:
   - Compare first name, last name, and full name
   - Handle variations: middle names, initials, nicknames
   - Check for name order differences (first/last vs last/first)
   - Be flexible with spacing, punctuation, and capitalization
   - Match confidence: Exact match (high), Close match (medium), Mismatch (low)

2. **Date Matching**:
   - Compare date of birth, issue dates, expiry dates
   - Handle different date formats (DD/MM/YYYY vs MM/DD/YYYY)
   - Allow for minor variations (e.g., 01/01/1990 vs 1/1/1990)
   - Check for logical consistency (e.g., expiry > issue date)
   - Match confidence: Exact match (high), Format difference (medium), Mismatch (low)

3. **Number Matching**:
   - Compare passport numbers, ID numbers, reference numbers
   - Handle formatting differences (spaces, dashes, case)
   - Check for partial matches (e.g., last 4 digits)
   - Match confidence: Exact match (high), Format difference (medium), Mismatch (low)

4. **Nationality/Country Matching**:
   - Compare nationality, country of birth, country codes
   - Handle variations: full names vs codes (e.g., "United Kingdom" vs "UK" vs "GB")
   - Check for ISO country codes vs country names
   - Match confidence: Exact match (high), Code variation (medium), Mismatch (low)

5. **Other Identifiers**:
   - Compare any other relevant identifiers (address, occupation, etc.)
   - Handle variations in formatting and presentation
   - Check for logical consistency

## Validation Status Determination:

- **"passed"**: All critical fields match with high confidence
  - All names match (exact or close)
  - All dates match (exact or format variation)
  - All numbers match (exact or format variation)
  - No critical mismatches found

- **"failed"**: Critical mismatches found
  - Name mismatch (different person)
  - Date mismatch (different date of birth)
  - Number mismatch (different passport/ID number)
  - Nationality mismatch (different country)

- **"warning"**: Minor issues or missing non-critical fields
  - Minor formatting differences
  - Missing optional fields
  - Low confidence matches
  - Ambiguous information

- **"pending"**: Cannot determine (insufficient information)
  - Document text too short or unclear
  - Missing critical information in document
  - OCR quality too poor to extract information

## Your Task:
Compare the document content with case facts and validate. Respond with ONLY valid JSON in this exact format:
{{
    "status": "passed" | "failed" | "warning" | "pending",
    "details": {{
        "matched_fields": [
            {{
                "field": "field_name",
                "document_value": "value from document",
                "case_value": "value from case",
                "confidence": 0.0-1.0,
                "match_type": "exact" | "close" | "format_variation"
            }}
        ],
        "mismatched_fields": [
            {{
                "field": "field_name",
                "document_value": "value from document",
                "case_value": "value from case",
                "confidence": 0.0-1.0,
                "mismatch_type": "different_value" | "format_error" | "missing_in_document"
            }}
        ],
        "missing_fields": [
            {{
                "field": "field_name",
                "expected_value": "value from case",
                "reason": "why field is missing"
            }}
        ],
        "confidence": 0.0-1.0,
        "summary": "Brief summary of validation results"
    }},
    "reasoning": "Detailed explanation of validation process, matches found, mismatches identified, and confidence assessment"
}}

**Important**: 
- Be precise and conservative in your validation
- Only mark as "passed" if you're highly confident
- Mark as "failed" if there are clear mismatches
- Provide detailed reasoning for your decisions
- Include confidence scores for each field match
- Only respond with valid JSON, no markdown, no additional text"""

    return prompt


def _get_validation_guidance(document_type_code: str = None) -> str:
    """Get document type specific guidance for content validation."""
    guidance_map = {
        'passport': """**Passport Validation**:
- Critical fields: Full name, date of birth, passport number, nationality, expiry date
- Check photo page information matches case facts
- Verify passport number format matches issuing country
- Ensure expiry date is valid and not expired
- Check for any annotations or restrictions""",
        
        'visa': """**Visa Validation**:
- Critical fields: Name, passport number, visa type, validity dates
- Verify visa holder name matches case facts
- Check visa validity period (from/to dates)
- Ensure visa type matches application type
- Verify passport number matches""",
        
        'bank_statement': """**Bank Statement Validation**:
- Critical fields: Account holder name, account number, statement period
- Verify account holder name matches case facts
- Check statement dates are recent and valid
- Ensure sufficient funds are shown
- Verify bank name and account details""",
        
        'certificate_of_sponsorship': """**Certificate of Sponsorship Validation**:
- Critical fields: Applicant name, sponsor name, certificate number, issue date
- Verify applicant name matches case facts
- Check certificate number format
- Ensure certificate is valid and not expired
- Verify sponsor details match application"""
    }
    
    if document_type_code and document_type_code.lower() in guidance_map:
        return guidance_map[document_type_code.lower()]
    
    return """**General Document Validation**:
- Compare all relevant fields from document with case facts
- Focus on identifying information: names, dates, numbers, identifiers
- Check for consistency and logical relationships
- Verify document authenticity indicators
- Ensure all critical information is present and matches"""


def get_content_validation_system_message() -> str:
    """
    Get system message for content validation.
    
    Returns:
        System message string
    """
    return (
        "You are a precise document validation expert for immigration visa applications. "
        "You compare document content with case facts and identify matches and mismatches. "
        "Be precise and conservative in your validation. "
        "Always respond with valid JSON only, no markdown formatting, no additional text."
    )


# Backward compatibility
def get_system_message() -> str:
    """Backward compatibility alias for get_classification_system_message."""
    return get_classification_system_message()

