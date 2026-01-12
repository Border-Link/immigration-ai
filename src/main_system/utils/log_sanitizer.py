"""
Log Sanitizer

Sanitizes sensitive information from log messages to prevent PII, secrets, and tokens
from being logged. This is critical for GDPR compliance and security.
"""
import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger('django')


class LogSanitizer:
    """
    Utility class for sanitizing sensitive data from logs.
    """
    
    # Patterns to detect and sanitize
    SENSITIVE_PATTERNS = [
        # Passwords
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'password": "***REDACTED***'),
        (r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'pwd": "***REDACTED***'),
        
        # API Keys and Tokens (generic patterns)
        (r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'\1": "***REDACTED***'),
        (r'(secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'\1": "***REDACTED***'),
        (r'(access[_-]?token|accesstoken)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'\1": "***REDACTED***'),
        (r'(refresh[_-]?token|refreshtoken)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'\1": "***REDACTED***'),
        (r'(bearer\s+)([a-zA-Z0-9\-_\.]+)', r'\1***REDACTED***'),
        
        # Specific API keys used in the system
        (r'(openai[_-]?api[_-]?key|OPENAI_API_KEY)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'OPENAI_API_KEY": "***REDACTED***'),
        (r'(stripe[_-]?(secret|public)[_-]?key|STRIPE_(SECRET|PUBLIC)_KEY)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'STRIPE_KEY": "***REDACTED***'),
        (r'(stripe[_-]?webhook[_-]?secret|STRIPE_WEBHOOK_SECRET)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'STRIPE_WEBHOOK_SECRET": "***REDACTED***'),
        (r'(paypal[_-]?(client[_-]?id|client[_-]?secret|webhook[_-]?id))["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'PAYPAL_KEY": "***REDACTED***'),
        (r'(adyen[_-]?api[_-]?key|ADYEN_API_KEY)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'ADYEN_API_KEY": "***REDACTED***'),
        (r'(mono[_-]?webhook[_-]?secret[_-]?key|MONO_WEBHOOK_SECRET_KEY)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'MONO_WEBHOOK_SECRET_KEY": "***REDACTED***'),
        (r'(open[_-]?exchange[_-]?rate[_-]?api[_-]?key)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'OPEN_EXCHANGE_RATE_API_KEY": "***REDACTED***'),
        (r'(sendgrid[_-]?api[_-]?key)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'SENDGRID_API_KEY": "***REDACTED***'),
        
        # Credit Card Numbers (basic pattern)
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', r'****-****-****-****'),
        
        # Email addresses (truncate domain)
        (r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', r'\1@***REDACTED***'),
        
        # Long tokens (UUIDs, hashes) - show first 4 and last 4 chars
        (r'\b([a-f0-9]{4})[a-f0-9]{24,}([a-f0-9]{4})\b', r'\1***REDACTED***\2'),
    ]
    
    # Fields that should always be redacted
    REDACT_FIELDS = [
        'password', 'pwd', 'secret', 'api_key', 'api-key', 'apikey',
        'access_token', 'access-token', 'refresh_token', 'refresh-token',
        'token', 'authorization', 'auth', 'credential', 'credentials',
        'credit_card', 'credit-card', 'card_number', 'card-number',
        'ssn', 'social_security', 'social-security',
        # Specific API keys used in the system
        'openai_api_key', 'openai-api-key', 'openai_apikey',
        'stripe_secret_key', 'stripe-secret-key', 'stripe_public_key', 'stripe-public-key',
        'stripe_webhook_secret', 'stripe-webhook-secret',
        'paypal_client_id', 'paypal-client-id', 'paypal_client_secret', 'paypal-client-secret',
        'paypal_webhook_id', 'paypal-webhook-id',
        'adyen_api_key', 'adyen-api-key', 'adyen_merchant_account',
        'mono_webhook_secret_key', 'mono-webhook-secret-key',
        'open_exchange_rate_api_key', 'open-exchange-rate-api-key',
        'sendgrid_api_key', 'sendgrid-api-key',
    ]
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """
        Sanitize a string by removing sensitive information.
        
        Args:
            text: String to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return text
        
        sanitized = text
        
        # Apply pattern-based sanitization
        for pattern, replacement in LogSanitizer.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a dictionary by removing or redacting sensitive fields.
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field should be redacted
            should_redact = any(
                redact_field in key_lower 
                for redact_field in LogSanitizer.REDACT_FIELDS
            )
            
            if should_redact:
                # Redact the value
                if isinstance(value, str) and len(value) > 8:
                    # Show first 4 and last 4 chars for long values
                    sanitized[key] = f"{value[:4]}***REDACTED***{value[-4:]}"
                else:
                    sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = LogSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    LogSanitizer.sanitize_dict(item) if isinstance(item, dict)
                    else LogSanitizer.sanitize_string(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Sanitize string values
                sanitized[key] = LogSanitizer.sanitize_string(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def sanitize_log_message(message: str, *args, **kwargs) -> tuple:
        """
        Sanitize log message and arguments.
        
        Args:
            message: Log message format string
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tuple of (sanitized_message, sanitized_args, sanitized_kwargs)
        """
        # Sanitize message
        sanitized_message = LogSanitizer.sanitize_string(message)
        
        # Sanitize args
        sanitized_args = tuple(
            LogSanitizer.sanitize_dict(arg) if isinstance(arg, dict)
            else LogSanitizer.sanitize_string(str(arg)) if isinstance(arg, str)
            else arg
            for arg in args
        )
        
        # Sanitize kwargs
        sanitized_kwargs = LogSanitizer.sanitize_dict(kwargs)
        
        return sanitized_message, sanitized_args, sanitized_kwargs
    
    @staticmethod
    def truncate_email(email: str) -> str:
        """
        Truncate email address to show only username part.
        
        Args:
            email: Email address
            
        Returns:
            Truncated email (e.g., "user@***")
        """
        if not isinstance(email, str) or '@' not in email:
            return email
        
        username, domain = email.split('@', 1)
        return f"{username}@***"
    
    @staticmethod
    def truncate_token(token: str, show_chars: int = 4) -> str:
        """
        Truncate token to show only first and last N characters.
        
        Args:
            token: Token string
            show_chars: Number of characters to show at start and end
            
        Returns:
            Truncated token (e.g., "abcd***xyz")
        """
        if not isinstance(token, str) or len(token) <= show_chars * 2:
            return "***REDACTED***"
        
        return f"{token[:show_chars]}***REDACTED***{token[-show_chars:]}"
