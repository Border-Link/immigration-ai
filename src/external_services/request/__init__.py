"""
External services request handlers.

All external requests (HTTP, LLM, etc.) should go through this module
to ensure consistent error handling, retry logic, rate limiting, and logging.
"""

from .http_client import ExternalHTTPClient
from .llm_client import ExternalLLMClient

__all__ = [
    'ExternalHTTPClient',
    'ExternalLLMClient',
]
