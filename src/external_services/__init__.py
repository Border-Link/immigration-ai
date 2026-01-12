"""
External services module.

Provides centralized handlers for all external service requests.
"""

from .request import (
    ExternalHTTPClient,
    ExternalLLMClient,
    ExternalSpeechToTextClient,
    ExternalTextToSpeechClient
)

__all__ = [
    'ExternalHTTPClient',
    'ExternalLLMClient',
    'ExternalSpeechToTextClient',
    'ExternalTextToSpeechClient',
]
