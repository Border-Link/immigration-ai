"""
Document Type Descriptions

Contains detailed descriptions and key indicators for different document types.
Used for document classification prompts.
"""

# Common document type descriptions with detailed characteristics
DOCUMENT_TYPE_DESCRIPTIONS = {
    'PASSPORT': {
        'description': 'Passport - Official travel document with photo, personal details, passport number, nationality, and expiry date',
        'key_indicators': [
            'Contains "PASSPORT", "PASSEPORT", "PASAPORTE"',
            'Passport number format (alphanumeric)',
            'Nationality/citizenship information',
            'Photo page with personal details',
            'Issuing authority (e.g., "United Kingdom", "HM Passport Office")',
            'Date of birth, place of birth',
            'Expiry date',
            'MRZ (machine readable zone)',
            'Personal identification number'
        ]
    },
    'BIRTH_CERTIFICATE': {
        'description': 'Birth Certificate - Official record of birth with date, place, parent names, and registration number',
        'key_indicators': [
            'Contains "BIRTH CERTIFICATE" or "CERTIFICATE OF BIRTH"',
            'Birth registration information',
            'Date and place of birth',
            'Parent names',
            'Registration number',
            'Issuing authority (e.g., "General Register Office", "Vital Records Office")',
            'Certificate number'
        ]
    },
    'BANK_STATEMENT': {
        'description': 'Bank Statement - Financial document showing account transactions, balances, and statement period',
        'key_indicators': [
            'Bank name and logo',
            'Account number (often partially masked)',
            'Statement period (e.g., "Statement Period: 01/01/2024 - 31/01/2024")',
            'Transaction history',
            'Opening/closing balance',
            'Account holder name',
            'Terms like "Opening Balance", "Closing Balance", "Deposits", "Withdrawals"',
            'Transaction dates and amounts'
        ]
    },
    'CERTIFICATE_OF_SPONSORSHIP': {
        'description': 'Certificate of Sponsorship (COS) - UK visa sponsorship certificate with job details, salary, and sponsor information',
        'key_indicators': [
            'Contains "CERTIFICATE OF SPONSORSHIP" or "COS"',
            'Sponsor license number',
            'Job title and SOC code',
            'Salary information',
            'Start date',
            'Sponsor name and address',
            'UKVI reference numbers',
            '"Skilled Worker" or visa route name',
            'Certificate number'
        ]
    },
    'EDUCATION_CERTIFICATE': {
        'description': 'Education Certificate - Degree, diploma, or qualification certificate from educational institution',
        'key_indicators': [
            'University/school name and logo',
            'Degree/diploma name',
            'Graduation date',
            'Student name',
            'Qualification level (e.g., "Bachelor", "Master", "PhD")',
            'Institution accreditation',
            'Transcript or certificate format',
            'Course name and duration'
        ]
    },
    'LANGUAGE_TEST': {
        'description': 'Language Test Certificate - English language proficiency test results (IELTS, TOEFL, PTE, etc.)',
        'key_indicators': [
            'Test provider name prominently displayed ("IELTS", "TOEFL", "PTE Academic", "Cambridge")',
            'Test date',
            'Candidate name and ID',
            'Score breakdown (Reading, Writing, Speaking, Listening)',
            'Overall band/score',
            'Test reference number',
            'Test center information',
            'Validity period'
        ]
    },
    'MARRIAGE_CERTIFICATE': {
        'description': 'Marriage Certificate - Official record of marriage with date, location, and spouse names',
        'key_indicators': [
            'Contains "MARRIAGE CERTIFICATE" or "CERTIFICATE OF MARRIAGE"',
            'Marriage date and location',
            'Spouse names',
            'Registration number',
            'Issuing authority (e.g., "General Register Office")',
            'Officiant name',
            'Witness names'
        ]
    },
    'EMPLOYMENT_LETTER': {
        'description': 'Employment Letter - Letter from employer confirming job title, salary, and employment details',
        'key_indicators': [
            'Company letterhead',
            'Employment start date',
            'Job title and responsibilities',
            'Salary information',
            'Employment status (full-time, part-time, contract)',
            'Manager/supervisor signature',
            'Company contact details',
            'Employment duration'
        ]
    },
    'ACCOMMODATION_EVIDENCE': {
        'description': 'Accommodation Evidence - Proof of housing (tenancy agreement, mortgage statement, property ownership)',
        'key_indicators': [
            'Property address',
            'Landlord/owner name',
            'Tenancy agreement or mortgage statement',
            'Property size (bedrooms, square footage)',
            'Monthly rent/mortgage amount',
            'Property ownership documents',
            'Council tax statements',
            'Lease dates'
        ]
    },
    'CRIMINAL_RECORD_CHECK': {
        'description': 'Criminal Record Check - DBS, CRB, or police certificate showing criminal record status',
        'key_indicators': [
            'Contains "DBS", "CRB", "POLICE CERTIFICATE", "CRIMINAL RECORD"',
            'Certificate number',
            'Issue date',
            'Issuing authority (police force name, DBS)',
            'Clearance status',
            'Applicant name',
            'Certificate type (Basic, Standard, Enhanced)'
        ]
    },
    'FINANCIAL_EVIDENCE': {
        'description': 'Financial Evidence - Proof of funds (bank statements, savings certificates, investment statements)',
        'key_indicators': [
            'Bank statements',
            'Savings certificates',
            'Investment statements',
            'Account balances',
            'Proof of income',
            'Financial sponsor letters',
            'Asset valuations',
            'Financial institution names'
        ]
    },
    'TRAVEL_HISTORY': {
        'description': 'Travel History - Passport stamps, travel records, or visa history',
        'key_indicators': [
            'Passport stamps',
            'Visa stickers',
            'Entry/exit stamps',
            'Travel dates',
            'Countries visited',
            'Previous visa documents',
            'Travel itinerary',
            'Immigration stamps'
        ]
    },
    'MEDICAL_CERTIFICATE': {
        'description': 'Medical Certificate - Health certificate, TB test results, or medical examination report',
        'key_indicators': [
            '"TB TEST", "MEDICAL EXAMINATION"',
            'Health certificate',
            'Test results',
            'Doctor/clinic name',
            'Test date',
            'Clearance status',
            'Medical examination report',
            'Test reference number'
        ]
    },
    'PHOTO_ID': {
        'description': 'Photo ID - Government-issued photo identification (driving license, national ID card)',
        'key_indicators': [
            'Government-issued photo ID',
            'Driving license',
            'National ID card',
            'Photo',
            'Personal details',
            'Issuing authority',
            'ID number',
            'Expiry date'
        ]
    },
    'PROOF_OF_ADDRESS': {
        'description': 'Proof of Address - Utility bills, council tax statements, or official correspondence showing address',
        'key_indicators': [
            'Utility bills (electricity, gas, water)',
            'Council tax statements',
            'Official correspondence',
            'Bank statements with address',
            'Tenancy agreements',
            'Address clearly displayed',
            'Issue date',
            'Service provider name'
        ]
    },
    'VISA_STAMP': {
        'description': 'Visa Stamp - Visa sticker or stamp in passport from previous travel',
        'key_indicators': [
            'Visa sticker in passport',
            'Visa stamp',
            'Visa number',
            'Country of issue',
            'Validity dates',
            'Visa type',
            'Entry/exit stamps',
            'Immigration officer stamp'
        ]
    },
    'SPONSOR_LETTER': {
        'description': 'Sponsor Letter - Letter from sponsor confirming support and relationship',
        'key_indicators': [
            'Letter from sponsor',
            'Relationship confirmation',
            'Support details',
            'Sponsor contact information',
            'Signature',
            'Date',
            'Sponsor name and address'
        ]
    },
    'DEPENDANT_DOCUMENTS': {
        'description': 'Dependant Documents - Documents for family members (birth certificates, marriage certificates for dependants)',
        'key_indicators': [
            'Documents for family members',
            'Birth certificates for children',
            'Marriage certificates',
            'Relationship proof',
            'Dependant visa documents',
            'Family member names',
            'Relationship to main applicant'
        ]
    },
}


def get_document_type_description(doc_type_code: str) -> dict:
    """
    Get description and key indicators for a document type.
    
    Args:
        doc_type_code: Document type code (e.g., 'PASSPORT', 'BANK_STATEMENT')
        
    Returns:
        Dict with 'description' and 'key_indicators', or None if not found
    """
    return DOCUMENT_TYPE_DESCRIPTIONS.get(doc_type_code.upper(), {
        'description': f'{doc_type_code} - Document type (analyze content for specific characteristics)',
        'key_indicators': []
    })


def format_document_types_for_prompt(possible_types: list) -> str:
    """
    Format document types with descriptions for LLM prompt.
    
    Args:
        possible_types: List of document type codes
        
    Returns:
        Formatted string with document type descriptions
    """
    if not possible_types:
        return "No document types available."
    
    type_list = []
    for doc_type in possible_types:
        doc_info = get_document_type_description(doc_type)
        description = doc_info['description']
        type_list.append(f"- **{doc_type}**: {description}")
    
    return '\n'.join(type_list) if type_list else "No document types available."

