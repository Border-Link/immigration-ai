"""
Custom exceptions for rule parsing service.

These exceptions allow for proper error classification and handling,
distinguishing between retryable and non-retryable errors.
"""


class RuleParsingError(Exception):
    """Base exception for rule parsing errors."""
    pass


class LLMRateLimitError(RuleParsingError):
    """Rate limit error from LLM API - retryable with backoff."""
    pass


class LLMTimeoutError(RuleParsingError):
    """Timeout error from LLM API - retryable."""
    pass


class LLMInvalidResponseError(RuleParsingError):
    """Invalid LLM response - not retryable."""
    pass


class LLMServiceUnavailableError(RuleParsingError):
    """LLM service unavailable - retryable."""
    pass


class LLMAPIKeyError(RuleParsingError):
    """Invalid or missing API key - not retryable."""
    pass


class JSONLogicValidationError(RuleParsingError):
    """Invalid JSON Logic expression - not retryable."""
    pass


class InsufficientTextError(RuleParsingError):
    """Insufficient text for parsing - not retryable."""
    pass


class RuleValidationError(RuleParsingError):
    """Rule data validation failed - not retryable."""
    pass


class DuplicateParsingError(RuleParsingError):
    """Document already parsed - not retryable."""
    pass
