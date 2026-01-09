"""
Constants for rule parsing service configuration.

This module contains configuration constants used by the RuleParsingService
for LLM calls, text processing, and validation.
"""

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# OpenAI Model Configuration
DEFAULT_LLM_MODEL = "gpt-4-turbo-preview"
FALLBACK_LLM_MODEL = "gpt-4"
LLM_TEMPERATURE = 0.2  # Lower temperature for more deterministic rule extraction
LLM_MAX_TOKENS = 3000  # Allow enough tokens for multiple requirements
LLM_TIMEOUT_SECONDS = 60.0  # Request timeout in seconds

# Text Processing
MAX_TEXT_LENGTH = 8000  # Characters to leave room for prompt (~2000 chars) and stay under token limit
MIN_TEXT_LENGTH = 50  # Minimum text length required for parsing

# ============================================================================
# CONFIDENCE SCORING
# ============================================================================

BASE_CONFIDENCE_SCORE = 0.5  # Base confidence score (50%)
NUMERIC_VALUE_MATCH_BONUS = 0.2  # Bonus if numeric values match source text
STANDARD_CODE_BONUS = 0.2  # Bonus if requirement code is a standard code
VALID_JSON_LOGIC_BONUS = 0.1  # Bonus if JSON Logic expression is valid and non-empty
MAX_CONFIDENCE_SCORE = 1.0  # Maximum confidence score cap

# ============================================================================
# SLA CONFIGURATION
# ============================================================================

DEFAULT_SLA_DAYS = 7  # Default SLA for validation (7 days)
URGENT_SLA_DAYS = 2  # Urgent SLA for high confidence rules (2 days)
HIGH_CONFIDENCE_THRESHOLD = 0.9  # Confidence score threshold for urgent SLA

# ============================================================================
# VALIDATION
# ============================================================================

# Minimum required fields for a valid rule
REQUIRED_RULE_FIELDS = [
    'requirement_code',
    'description',
    'condition_expression',
]

# Valid JSON Logic operators (for validation)
VALID_JSON_LOGIC_OPERATORS = [
    '==', '!=', '>', '>=', '<', '<=',  # Comparison
    'and', 'or', '!',  # Logical
    'var',  # Variable access
    '+', '-', '*', '/', '%',  # Arithmetic
    'if',  # Conditional
    'in', 'cat', 'substr',  # String/Array operations
]
