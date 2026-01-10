"""
External services module.

Provides centralized handlers for all external service requests.
"""

from .request import ExternalHTTPClient, ExternalLLMClient

__all__ = [
    'ExternalHTTPClient',
    'ExternalLLMClient',
]
