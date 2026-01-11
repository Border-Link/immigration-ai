"""
Custom exceptions for payment gateway operations.

These exceptions allow for proper error classification and handling,
distinguishing between retryable and non-retryable errors.
"""


class PaymentGatewayError(Exception):
    """Base exception for payment gateway errors."""
    pass


class PaymentGatewayConfigurationError(PaymentGatewayError):
    """Configuration error - missing API keys, invalid settings, etc. Non-retryable."""
    pass


class PaymentGatewayAuthenticationError(PaymentGatewayError):
    """Authentication error - invalid API keys, expired tokens, etc. Non-retryable."""
    pass


class PaymentGatewayRateLimitError(PaymentGatewayError):
    """Rate limit error from payment gateway - retryable with backoff."""
    pass


class PaymentGatewayTimeoutError(PaymentGatewayError):
    """Timeout error from payment gateway - retryable."""
    pass


class PaymentGatewayServiceUnavailableError(PaymentGatewayError):
    """Service unavailable error - retryable."""
    pass


class PaymentGatewayInvalidResponseError(PaymentGatewayError):
    """Invalid response from payment gateway - may be retryable depending on context."""
    pass


class PaymentGatewayValidationError(PaymentGatewayError):
    """Validation error - invalid payment data, amount, etc. Non-retryable."""
    pass


class PaymentGatewayNetworkError(PaymentGatewayError):
    """Network error - connection issues, DNS failures, etc. Retryable."""
    pass
