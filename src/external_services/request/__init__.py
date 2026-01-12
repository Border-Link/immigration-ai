"""
External services request handlers.

All external requests (HTTP, LLM, etc.) should go through this module
to ensure consistent error handling, retry logic, rate limiting, and logging.
"""

from .http_client import ExternalHTTPClient
from .llm_client import ExternalLLMClient
from .speech_client import ExternalSpeechToTextClient
from .tts_client import ExternalTextToSpeechClient

__all__ = [
    'ExternalHTTPClient',
    'ExternalLLMClient',
    'ExternalSpeechToTextClient',
    'ExternalTextToSpeechClient',
]
