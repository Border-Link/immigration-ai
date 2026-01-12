"""
Constants for case context building.

Contains static data used in context bundle construction:
- Allowed topics for AI conversations
- Restricted topics that should be blocked
- Context bundle field requirements
"""

# Allowed topics for AI call conversations
ALLOWED_TOPICS = [
    'eligibility',
    'documents',
    'timeline',
    'next_steps',
    'requirements'
]

# Restricted topics that should be blocked or refused
RESTRICTED_TOPICS = [
    # Legal authority & advice
    'legal advice',
    'personalized legal advice',
    'legal strategy',
    'acting as a lawyer',
    'representation guidance',
    # Guarantees & predictions
    'legal guarantees',
    'application approval',
    'approval likelihood',
    'success probability',
    'guaranteed outcomes',
    'case outcomes',
    # Visa recommendations
    'visa recommendations',
    'other visas',
    'alternative visa routes',
    'best visa option',
    'visa switching advice',
    # Case-specific judgments
    'eligibility confirmation',
    'eligibility denial',
    'case assessment',
    'individual case evaluation',
    # Appeals & enforcement
    'appeal strategies',
    'refusal challenge guidance',
    'judicial review advice',
    'deportation defense',
    # Fraud & evasion
    'bypassing immigration rules',
    'loopholes',
    'misrepresentation guidance',
    'false statements',
    'hiding information',
    # Authority impersonation
    'official decisions',
    'government authority claims',
    'immigration officer role',
    # Decision influence
    'influencing officers',
    'persuasive approval arguments',
    # Timelines & pressure
    'guaranteed processing times',
    'fast-track promises',
    'urgency pressure',
    # Sensitive decisions
    'life-altering decisions',
    'irreversible immigration choices',
    # Enforcement speculation
    'enforcement likelihood',
    'profiling speculation',
    # Financial guarantees
    'fee guarantees',
    'outcome-based payment',
    # Minor-specific restrictions
    'minor independent legal action',
    'parental consent avoidance'
]

# Required fields in context bundle for validation
REQUIRED_CONTEXT_FIELDS = [
    'case_id',
    'case_facts',
    'documents_summary'
]

# Default case type
DEFAULT_CASE_TYPE = 'ImmigrationCase'

# Default context version
DEFAULT_CONTEXT_VERSION = 1
