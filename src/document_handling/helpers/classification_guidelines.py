"""
Classification Guidelines

Contains classification rules, confidence scoring guidelines, and edge case handling
instructions for document classification.
"""

# Classification guidelines sections
CLASSIFICATION_GUIDELINES = {
    'key_indicators': """1. **Key Indicators to Look For**:
   - Document headers, titles, and official seals
   - Issuing authority names (e.g., "Home Office", "HM Passport Office", "Bank Name")
   - Document numbers (passport numbers, account numbers, reference numbers)
   - Dates (issue dates, expiry dates, statement periods)
   - Personal information (names, addresses, dates of birth)
   - Specific terminology unique to document types""",

    'confidence_scoring': """2. **Confidence Scoring**:
   - **0.9-1.0 (Very High)**: Clear, unambiguous document with multiple strong indicators
   - **0.7-0.89 (High)**: Strong indicators present, minor ambiguity possible
   - **0.5-0.69 (Medium)**: Some indicators present but not definitive
   - **0.0-0.49 (Low)**: Unclear or insufficient information""",

    'edge_cases': """3. **Edge Cases to Handle**:
   - **Multiple document types in one file**: Classify the primary/most important document
   - **Partial documents**: Classify based on visible content, lower confidence if incomplete
   - **Scanned/photocopied documents**: May have OCR errors, focus on key phrases
   - **Multi-language documents**: Classify based on structure and recognizable terms
   - **Unclear content**: If truly ambiguous, choose the most likely type with lower confidence""",

    'classification_rules': """5. **Classification Rules**:
   - Match the document to the MOST SPECIFIC type available
   - If document could match multiple types, choose the one with strongest indicators
   - Consider the filename as a hint but prioritize document content
   - If truly uncertain, choose the most likely type but set confidence < 0.7"""
}


def get_classification_guidelines() -> str:
    """
    Get formatted classification guidelines for LLM prompt.
    
    Returns:
        Formatted string with all classification guidelines
    """
    return '\n\n'.join([
        CLASSIFICATION_GUIDELINES['key_indicators'],
        CLASSIFICATION_GUIDELINES['confidence_scoring'],
        CLASSIFICATION_GUIDELINES['edge_cases'],
        CLASSIFICATION_GUIDELINES['classification_rules']
    ])


# Common document type indicators (detailed)
COMMON_DOCUMENT_INDICATORS = {
    'PASSPORT': """   **PASSPORT**: 
   - Contains "PASSPORT", "PASSEPORT", "PASAPORTE"
   - Passport number format (alphanumeric)
   - Nationality/citizenship information
   - Photo page with personal details
   - Issuing authority (e.g., "United Kingdom", "HM Passport Office")
   - Date of birth, place of birth
   - Expiry date""",

    'BIRTH_CERTIFICATE': """   **BIRTH_CERTIFICATE**:
   - Contains "BIRTH CERTIFICATE", "CERTIFICATE OF BIRTH"
   - Birth registration information
   - Date and place of birth
   - Parent names
   - Registration number
   - Issuing authority (e.g., "General Register Office", "Vital Records")""",

    'BANK_STATEMENT': """   **BANK_STATEMENT**:
   - Bank name and logo
   - Account number (partially masked)
   - Statement period (e.g., "Statement Period: 01/01/2024 - 31/01/2024")
   - Transaction history
   - Balance information
   - Account holder name
   - Terms like "Opening Balance", "Closing Balance", "Deposits", "Withdrawals" """,

    'CERTIFICATE_OF_SPONSORSHIP': """   **CERTIFICATE_OF_SPONSORSHIP**:
   - Contains "CERTIFICATE OF SPONSORSHIP", "COS"
   - Sponsor license number
   - Job title and SOC code
   - Salary information
   - Start date
   - Sponsor name and address
   - UKVI reference numbers""",

    'EDUCATION_CERTIFICATE': """   **EDUCATION_CERTIFICATE**:
   - University/school name and logo
   - Degree/diploma name
   - Graduation date
   - Student name
   - Qualification level (e.g., "Bachelor", "Master", "PhD")
   - Institution accreditation""",

    'LANGUAGE_TEST': """   **LANGUAGE_TEST**:
   - Test provider name (e.g., "IELTS", "TOEFL", "PTE Academic")
   - Test date and results
   - Candidate name and ID
   - Score breakdown (Reading, Writing, Speaking, Listening)
   - Test reference number""",

    'MARRIAGE_CERTIFICATE': """   **MARRIAGE_CERTIFICATE**:
   - Contains "MARRIAGE CERTIFICATE", "CERTIFICATE OF MARRIAGE"
   - Marriage date and location
   - Spouse names
   - Registration number
   - Issuing authority""",

    'EMPLOYMENT_LETTER': """   **EMPLOYMENT_LETTER**:
   - Company letterhead
   - Employment start date
   - Job title and responsibilities
   - Salary information
   - Employment status (full-time, part-time)
   - Manager/supervisor signature""",

    'ACCOMMODATION_EVIDENCE': """   **ACCOMMODATION_EVIDENCE**:
   - Property address
   - Landlord/owner name
   - Tenancy agreement or ownership documents
   - Property size (bedrooms, square footage)
   - Monthly rent/mortgage amount""",

    'CRIMINAL_RECORD_CHECK': """   **CRIMINAL_RECORD_CHECK**:
   - Contains "DBS", "CRB", "POLICE CERTIFICATE", "CRIMINAL RECORD"
   - Certificate number
   - Issue date
   - Issuing authority (police force, DBS)
   - Clearance status"""
}


def get_common_document_indicators() -> str:
    """
    Get formatted common document type indicators for LLM prompt.
    
    Returns:
        Formatted string with document type indicators
    """
    return '\n\n'.join(COMMON_DOCUMENT_INDICATORS.values())


def get_document_indicators_for_types(possible_types: list) -> str:
    """
    Get document indicators for specific document types.
    
    Args:
        possible_types: List of document type codes
        
    Returns:
        Formatted string with indicators for the specified types
    """
    if not possible_types:
        return ""
    
    indicators = []
    for doc_type in possible_types:
        doc_type_upper = doc_type.upper()
        if doc_type_upper in COMMON_DOCUMENT_INDICATORS:
            indicators.append(COMMON_DOCUMENT_INDICATORS[doc_type_upper])
    
    return '\n\n'.join(indicators) if indicators else ""

