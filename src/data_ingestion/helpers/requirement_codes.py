"""
Standard requirement codes for immigration rule extraction.

This module contains comprehensive lists of standard requirement codes
used across different jurisdictions (UK, US, CA, AU) for immigration rules.
These codes are used for confidence scoring and validation in rule parsing.
"""

# ============================================================================
# ELIGIBILITY REQUIREMENT CODES
# ============================================================================

# Salary & Income Requirements
SALARY_CODES = [
    'MIN_SALARY',
    'MAX_SALARY',
    'SALARY_THRESHOLD',
    'ANNUAL_SALARY',
    'GROSS_SALARY',
    'NET_SALARY',
    'SALARY_RANGE',
    'INCOME_REQUIREMENT',
    'MIN_INCOME',
    'MAX_INCOME',
]

# Age Requirements
AGE_CODES = [
    'AGE_MIN',
    'AGE_MAX',
    'AGE_RANGE',
    'AGE_LIMIT',
    'MIN_AGE',
    'MAX_AGE',
    'AGE_REQUIREMENT',
]

# Experience & Qualifications
EXPERIENCE_CODES = [
    'YEARS_EXPERIENCE',
    'YEARS_EXPERIENCE_REQUIRED',
    'MIN_EXPERIENCE',
    'WORK_EXPERIENCE',
    'PROFESSIONAL_EXPERIENCE',
    'QUALIFICATION_LEVEL',
    'EDUCATION_LEVEL',
    'DEGREE_REQUIRED',
    'QUALIFICATION_REQUIRED',
    'PROFESSIONAL_QUALIFICATION',
]

# Sponsor Requirements
SPONSOR_CODES = [
    'HAS_VALID_SPONSOR',
    'SPONSOR_LICENSE',
    'SPONSOR_REQUIRED',
    'SPONSOR_APPROVED',
    'CERTIFICATE_OF_SPONSORSHIP',
    'COS_REQUIRED',
    'SPONSOR_LETTER',
    'EMPLOYER_SPONSOR',
]

# Language Requirements
LANGUAGE_CODES = [
    'ENGLISH_LANGUAGE_LEVEL',
    'LANGUAGE_REQUIREMENT',
    'LANGUAGE_TEST',
    'IELTS_SCORE',
    'TOEFL_SCORE',
    'PTE_SCORE',
    'LANGUAGE_CERTIFICATE',
    'MIN_LANGUAGE_SCORE',
]

# Financial Requirements
FINANCIAL_CODES = [
    'FUNDS_REQUIRED',
    'MIN_FUNDS',
    'BANK_BALANCE',
    'PROOF_OF_FUNDS',
    'MAINTENANCE_FUNDS',
    'SUFFICIENT_FUNDS',
    'FINANCIAL_REQUIREMENT',
    'BANK_STATEMENT',
    'FINANCIAL_CAPACITY',
]

# Nationality & Origin
NATIONALITY_CODES = [
    'NATIONALITY',
    'COUNTRY_OF_ORIGIN',
    'CITIZENSHIP',
    'RESIDENCE_COUNTRY',
    'ELIGIBLE_COUNTRY',
]

# Health & Medical
HEALTH_CODES = [
    'HEALTH_CHECK',
    'MEDICAL_EXAMINATION',
    'TB_TEST',
    'HEALTH_CERTIFICATE',
    'MEDICAL_CLEARANCE',
    'HEALTH_REQUIREMENT',
]

# Character & Criminal
CHARACTER_CODES = [
    'CHARACTER_REQUIREMENT',
    'CRIMINAL_RECORD_CHECK',
    'POLICE_CLEARANCE',
    'GOOD_CHARACTER',
    'NO_CRIMINAL_RECORD',
    'DBS_CHECK',
]

# Employment & Job
EMPLOYMENT_CODES = [
    'JOB_OFFER',
    'EMPLOYMENT_CONTRACT',
    'JOB_TITLE',
    'SOC_CODE',
    'OCCUPATION_CODE',
    'SKILL_LEVEL',
    'EMPLOYMENT_REQUIRED',
]

# Family & Dependants
FAMILY_CODES = [
    'DEPENDANT_ALLOWED',
    'SPOUSE_REQUIRED',
    'CHILDREN_ALLOWED',
    'FAMILY_REUNIFICATION',
    'DEPENDANT_VISA',
]

# ============================================================================
# DOCUMENT REQUIREMENT CODES
# ============================================================================

DOCUMENT_CODES = [
    'DOCUMENT_REQUIRED',
    'DOCUMENT_PASSPORT',
    'DOCUMENT_DEGREE',
    'DOCUMENT_FUNDS',
    'DOCUMENT_CERTIFICATE',
    'DOCUMENT_PROOF',
    'DOCUMENT_BIRTH_CERTIFICATE',
    'DOCUMENT_MARRIAGE_CERTIFICATE',
    'DOCUMENT_DIVORCE_CERTIFICATE',
    'DOCUMENT_DEATH_CERTIFICATE',
    'DOCUMENT_EDUCATION',
    'DOCUMENT_QUALIFICATION',
    'DOCUMENT_LANGUAGE_TEST',
    'DOCUMENT_CRIMINAL_RECORD',
    'DOCUMENT_POLICE_CLEARANCE',
    'DOCUMENT_MEDICAL',
    'DOCUMENT_TB_TEST',
    'DOCUMENT_BANK_STATEMENT',
    'DOCUMENT_EMPLOYMENT_LETTER',
    'DOCUMENT_EMPLOYMENT_CONTRACT',
    'DOCUMENT_SPONSOR_LETTER',
    'DOCUMENT_COS',
    'DOCUMENT_PHOTO',
    'DOCUMENT_ID',
    'DOCUMENT_ADDRESS_PROOF',
    'DOCUMENT_TRAVEL_HISTORY',
]

# ============================================================================
# FEE REQUIREMENT CODES
# ============================================================================

FEE_CODES = [
    'FEE_AMOUNT',
    'FEE_APPLICATION',
    'FEE_PROCESSING',
    'FEE_HEALTH_SURCHARGE',
    'FEE_IHS',
    'FEE_IMMIGRATION_HEALTH_SURCHARGE',
    'FEE_PRIORITY',
    'FEE_SUPER_PRIORITY',
    'FEE_PREMIUM',
    'FEE_BIOMETRIC',
    'FEE_VISA',
    'FEE_EXTENSION',
    'FEE_VARIATION',
    'FEE_SETTLEMENT',
    'FEE_CITIZENSHIP',
    'FEE_REFUND',
]

# ============================================================================
# PROCESSING TIME CODES
# ============================================================================

PROCESSING_TIME_CODES = [
    'PROCESSING_TIME_DAYS',
    'PROCESSING_TIME_WEEKS',
    'PROCESSING_TIME_MONTHS',
    'PROCESSING_DEADLINE',
    'PROCESSING_TIMEFRAME',
    'DECISION_TIME',
    'PROCESSING_PERIOD',
    'TURNAROUND_TIME',
    'PRIORITY_PROCESSING',
    'STANDARD_PROCESSING',
    'EXPEDITED_PROCESSING',
]

# ============================================================================
# OTHER REQUIREMENT CODES
# ============================================================================

OTHER_CODES = [
    'VALIDITY_PERIOD',
    'VISA_DURATION',
    'STAY_PERIOD',
    'ENTRY_REQUIREMENT',
    'EXIT_REQUIREMENT',
    'TRAVEL_RESTRICTION',
    'WORK_PERMISSION',
    'STUDY_PERMISSION',
    'NO_PUBLIC_FUNDS',
    'BIOMETRIC_REQUIRED',
    'INTERVIEW_REQUIRED',
    'APPEAL_RIGHT',
    'ADMINISTRATIVE_REVIEW',
]

# ============================================================================
# COMPREHENSIVE STANDARD CODES LIST
# ============================================================================

STANDARD_REQUIREMENT_CODES = (
    SALARY_CODES +
    AGE_CODES +
    EXPERIENCE_CODES +
    SPONSOR_CODES +
    LANGUAGE_CODES +
    FINANCIAL_CODES +
    NATIONALITY_CODES +
    HEALTH_CODES +
    CHARACTER_CODES +
    EMPLOYMENT_CODES +
    FAMILY_CODES +
    DOCUMENT_CODES +
    FEE_CODES +
    PROCESSING_TIME_CODES +
    OTHER_CODES
)

# Convert to set for faster lookups
STANDARD_REQUIREMENT_CODES_SET = set(STANDARD_REQUIREMENT_CODES)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_standard_requirement_code(code: str) -> bool:
    """
    Check if a requirement code is a standard code.
    
    Args:
        code: Requirement code to check (case-insensitive)
        
    Returns:
        True if code is a standard code, False otherwise
    """
    if not code:
        return False
    return code.upper() in STANDARD_REQUIREMENT_CODES_SET


def get_requirement_code_category(code: str) -> str:
    """
    Get the category of a requirement code.
    
    Args:
        code: Requirement code
        
    Returns:
        Category name (e.g., 'salary', 'age', 'document', 'fee')
    """
    if not code:
        return 'unknown'
    
    code_upper = code.upper()
    
    if code_upper in SALARY_CODES:
        return 'salary'
    elif code_upper in AGE_CODES:
        return 'age'
    elif code_upper in EXPERIENCE_CODES:
        return 'experience'
    elif code_upper in SPONSOR_CODES:
        return 'sponsor'
    elif code_upper in LANGUAGE_CODES:
        return 'language'
    elif code_upper in FINANCIAL_CODES:
        return 'financial'
    elif code_upper in NATIONALITY_CODES:
        return 'nationality'
    elif code_upper in HEALTH_CODES:
        return 'health'
    elif code_upper in CHARACTER_CODES:
        return 'character'
    elif code_upper in EMPLOYMENT_CODES:
        return 'employment'
    elif code_upper in FAMILY_CODES:
        return 'family'
    elif code_upper in DOCUMENT_CODES:
        return 'document'
    elif code_upper in FEE_CODES:
        return 'fee'
    elif code_upper in PROCESSING_TIME_CODES:
        return 'processing_time'
    elif code_upper in OTHER_CODES:
        return 'other'
    else:
        return 'unknown'


def get_codes_by_category(category: str) -> list:
    """
    Get all requirement codes for a specific category.
    
    Args:
        category: Category name (e.g., 'salary', 'document', 'fee')
        
    Returns:
        List of requirement codes in that category
    """
    category_map = {
        'salary': SALARY_CODES,
        'age': AGE_CODES,
        'experience': EXPERIENCE_CODES,
        'sponsor': SPONSOR_CODES,
        'language': LANGUAGE_CODES,
        'financial': FINANCIAL_CODES,
        'nationality': NATIONALITY_CODES,
        'health': HEALTH_CODES,
        'character': CHARACTER_CODES,
        'employment': EMPLOYMENT_CODES,
        'family': FAMILY_CODES,
        'document': DOCUMENT_CODES,
        'fee': FEE_CODES,
        'processing_time': PROCESSING_TIME_CODES,
        'other': OTHER_CODES,
    }
    return category_map.get(category.lower(), [])
