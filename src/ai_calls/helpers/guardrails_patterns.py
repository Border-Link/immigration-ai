"""
Guardrails patterns and rules for comprehensive validation.

Contains all patterns, keywords, and rules used by GuardrailsService
for pre-prompt and post-response validation.
"""
import re
from typing import List, Dict, Tuple

# Compiled regex patterns for performance
PUNCTUATION_PATTERN = re.compile(r'[^\w\s]')
WHITESPACE_PATTERN = re.compile(r'\s+')

# ============================================================================
# PRE-PROMPT VALIDATION PATTERNS
# ============================================================================

# Legal advice request patterns (user input)
LEGAL_ADVICE_PATTERNS = [
    r'\bshould\s+i\b',
    r'\bmust\s+i\b',
    r'\blegally\s+required\b',
    r'\blegal\s+obligation\b',
    r'\blaw\s+says\b',
    r'\bam\s+i\s+legally\b',
    r'\bdo\s+i\s+have\s+a\s+legal\b',
    r'\bis\s+it\s+legal\b',
    r'\bwhat\s+does\s+the\s+law\b',
    r'\baccording\s+to\s+law\b',
    r'\blegal\s+requirement\b',
    r'\blegally\s+obligated\b',
    r'\blegally\s+bound\b',
    r'\brequired\s+by\s+law\b',
    r'\bwhat\s+are\s+my\s+legal\s+rights\b',
    r'\bwhat\s+are\s+my\s+legal\s+obligations\b',
]

# Guarantee request patterns (user input)
GUARANTEE_REQUEST_PATTERNS = [
    r'\bguarantee\b',
    r'\bguaranteed\b',
    r'\bwill\s+be\s+approved\b',
    r'\bwill\s+succeed\b',
    r'\bdefinitely\b',
    r'\bcertain\b',
    r'\bassured\b',
    r'\b100%\s+chance\b',
    r'\bguaranteed\s+approval\b',
    r'\bguaranteed\s+success\b',
    r'\bwill\s+definitely\b',
    r'\bfor\s+sure\b',
    r'\bno\s+doubt\b',
    r'\babsolutely\s+certain\b',
    r'\bpositive\s+outcome\b',
]

# Other visa/case discussion patterns
OTHER_VISA_PATTERNS = [
    r'\bother\s+visa\b',
    r'\bdifferent\s+visa\b',
    r'\balternative\s+visa\b',
    r'\bbetter\s+visa\b',
    r'\bswitch\s+visa\b',
    r'\bchange\s+visa\b',
    r'\bvisa\s+switch\b',
    r'\bvisa\s+change\b',
    r'\bother\s+case\b',
    r'\bdifferent\s+case\b',
    r'\bsomeone\s+else\s+case\b',
]

# Fraud/evasion patterns (high priority - immediate refuse)
FRAUD_PATTERNS = [
    r'\bbypass\b',
    r'\bloophole\b',
    r'\bworkaround\b',
    r'\bhide\b',
    r'\bconceal\b',
    r'\bwithhold\s+information\b',
    r'\bfalse\s+statement\b',
    r'\bfake\s+document\b',
    r'\bfraudulent\b',
    r'\bmisrepresent\b',
    r'\blie\s+about\b',
    r'\bnot\s+tell\b',
    r'\bkeep\s+secret\b',
]

# Financial guarantee patterns
FINANCIAL_GUARANTEE_PATTERNS = [
    r'\bfee\s+guarantee\b',
    r'\boutcome\s+based\s+payment\b',
    r'\bpay\s+if\s+approved\b',
    r'\bno\s+win\s+no\s+fee\b',
    r'\bcontingency\s+fee\b',
]

# ============================================================================
# POST-RESPONSE VALIDATION PATTERNS
# ============================================================================

# Legal advice language patterns (AI response)
LEGAL_ADVICE_LANGUAGE_PATTERNS = [
    r'\byou\s+must\b',
    r'\byou\s+are\s+required\s+by\s+law\b',
    r'\blegal\s+obligation\b',
    r'\blegally\s+bound\b',
    r'\byou\s+are\s+legally\s+required\b',
    r'\bthe\s+law\s+requires\b',
    r'\baccording\s+to\s+the\s+law\b',
    r'\blegally\s+mandatory\b',
    r'\byou\s+have\s+a\s+legal\s+duty\b',
    r'\byou\s+must\s+legally\b',
]

# Guarantee language patterns (AI response)
GUARANTEE_LANGUAGE_PATTERNS = [
    r'\bguaranteed\b',
    r'\bwill\s+definitely\b',
    r'\bcertain\s+to\b',
    r'\bassured\b',
    r'\b100%\s+guarantee\b',
    r'\bguaranteed\s+approval\b',
    r'\bguaranteed\s+success\b',
    r'\bfor\s+sure\b',
    r'\bno\s+doubt\b',
    r'\babsolutely\s+certain\b',
    r'\bwill\s+absolutely\b',
    r'\bwill\s+undoubtedly\b',
    r'\bpositive\s+outcome\s+guaranteed\b',
]

# Proactive suggestion patterns (reactive-only violation)
PROACTIVE_PATTERNS = [
    r'\bwould\s+you\s+like\s+to\s+know\b',
    r'\blet\s+me\s+tell\s+you\b',
    r'\bi\s+should\s+mention\b',
    r'\byou\s+might\s+want\s+to\s+know\b',
    r'\bi\s+can\s+also\s+help\s+you\b',
    r'\bwould\s+you\s+be\s+interested\b',
    r'\blet\s+me\s+also\s+share\b',
    r'\bi\s+should\s+also\s+tell\b',
    r'\bby\s+the\s+way\b',
    r'\bwhile\s+we\s+are\s+at\s+it\b',
    r'\bhere\s+is\s+something\s+else\b',
    r'\bi\s+think\s+you\s+should\s+know\b',
    r'\byou\s+should\s+also\s+consider\b',
    r'\bhave\s+you\s+considered\b',
    r'\bmay\s+i\s+suggest\b',
]

# Safety language patterns (required in responses)
SAFETY_LANGUAGE_PATTERNS = [
    r'\bbased\s+on\s+your\s+case\s+information\b',
    r'\bbased\s+on\s+your\s+case\b',
    r'\baccording\s+to\s+your\s+case\b',
    r'\bper\s+your\s+case\s+details\b',
    r'\baccording\s+to\s+the\s+provided\s+information\b',
    r'\bbased\s+on\s+the\s+case\s+data\b',
    r'\baccording\s+to\s+your\s+provided\s+information\b',
]

# Off-scope topic patterns (AI response)
OFF_SCOPE_PATTERNS = [
    r'\bother\s+visa\s+types\b',
    r'\bdifferent\s+visa\s+options\b',
    r'\balternative\s+visa\s+routes\b',
    r'\bother\s+cases\b',
    r'\bgeneral\s+immigration\s+advice\b',
]

# Authority impersonation patterns
AUTHORITY_PATTERNS = [
    r'\bi\s+am\s+an\s+immigration\s+officer\b',
    r'\bwe\s+are\s+the\s+government\b',
    r'\bofficial\s+decision\b',
    r'\bgovernment\s+authority\b',
    r'\bimmigration\s+authority\b',
    r'\bwe\s+have\s+decided\b',
    r'\bwe\s+will\s+approve\b',
    r'\bwe\s+will\s+deny\b',
]

# ============================================================================
# COMPILED REGEX PATTERNS (for performance)
# ============================================================================

# Compile all patterns for performance
COMPILED_LEGAL_ADVICE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in LEGAL_ADVICE_PATTERNS]
COMPILED_GUARANTEE_REQUEST_PATTERNS = [re.compile(p, re.IGNORECASE) for p in GUARANTEE_REQUEST_PATTERNS]
COMPILED_OTHER_VISA_PATTERNS = [re.compile(p, re.IGNORECASE) for p in OTHER_VISA_PATTERNS]
COMPILED_FRAUD_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FRAUD_PATTERNS]
COMPILED_FINANCIAL_GUARANTEE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FINANCIAL_GUARANTEE_PATTERNS]

COMPILED_LEGAL_ADVICE_LANGUAGE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in LEGAL_ADVICE_LANGUAGE_PATTERNS]
COMPILED_GUARANTEE_LANGUAGE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in GUARANTEE_LANGUAGE_PATTERNS]
COMPILED_PROACTIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROACTIVE_PATTERNS]
COMPILED_SAFETY_LANGUAGE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SAFETY_LANGUAGE_PATTERNS]
COMPILED_OFF_SCOPE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in OFF_SCOPE_PATTERNS]
COMPILED_AUTHORITY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in AUTHORITY_PATTERNS]

# ============================================================================
# VIOLATION CATEGORIES
# ============================================================================

VIOLATION_CATEGORIES = {
    'legal_advice': {
        'severity': 'high',
        'action': 'refuse',
        'message': 'I cannot provide legal advice. This is informational guidance only.'
    },
    'guarantee': {
        'severity': 'high',
        'action': 'refuse',
        'message': 'I cannot provide guarantees about application outcomes.'
    },
    'fraud': {
        'severity': 'critical',
        'action': 'refuse',
        'message': 'I cannot assist with activities that may violate immigration laws.'
    },
    'other_visa': {
        'severity': 'medium',
        'action': 'refuse',
        'message': 'I can only discuss information related to your current case.'
    },
    'financial_guarantee': {
        'severity': 'high',
        'action': 'refuse',
        'message': 'I cannot provide financial guarantees or outcome-based payment arrangements.'
    },
    'proactive': {
        'severity': 'medium',
        'action': 'sanitize',
        'message': 'Response contains proactive suggestions (reactive-only model violation).'
    },
    'missing_safety_language': {
        'severity': 'low',
        'action': 'sanitize',
        'message': 'Response missing required safety language.'
    },
    'authority_impersonation': {
        'severity': 'critical',
        'action': 'refuse',
        'message': 'Response contains authority impersonation language.'
    },
    'off_scope': {
        'severity': 'medium',
        'action': 'sanitize',
        'message': 'Response discusses topics outside case scope.'
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for pattern matching."""
    if not text:
        return ''
    # Remove punctuation and normalize whitespace
    text = PUNCTUATION_PATTERN.sub(' ', text)
    text = WHITESPACE_PATTERN.sub(' ', text)
    return text.lower().strip()

def check_patterns(text: str, patterns: List[re.Pattern]) -> bool:
    """Check if any pattern matches in text."""
    normalized = normalize_text(text)
    return any(pattern.search(normalized) for pattern in patterns)

def find_matching_patterns(text: str, patterns: List[re.Pattern]) -> List[str]:
    """Find all matching patterns in text."""
    normalized = normalize_text(text)
    matches = []
    for pattern in patterns:
        if pattern.search(normalized):
            matches.append(pattern.pattern)
    return matches
