"""
LLM client wrapper for external LLM API requests.

Provides a centralized interface for LLM API calls through external_services.
All LLM requests should go through this client.
"""

import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from data_ingestion.helpers.llm_client import LLMClient as InternalLLMClient
from data_ingestion.exceptions.rule_parsing_exceptions import (
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceUnavailableError,
    LLMAPIKeyError,
    LLMInvalidResponseError
)

logger = logging.getLogger('django')


class ExternalLLMClient:
    """
    External LLM client wrapper.
    
    This wraps the internal LLMClient to ensure all LLM requests
    go through the external_services layer for consistency.
    """
    
    def __init__(self):
        """Initialize external LLM client."""
        self._internal_client = InternalLLMClient()
    
    def extract_rules(
        self,
        extracted_text: str,
        jurisdiction: str = 'UK',
        model: Optional[str] = None,
        use_fallback: bool = True,
        document_version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract rules from text using LLM.
        
        Args:
            extracted_text: Text to extract rules from
            jurisdiction: Jurisdiction code (UK, US, etc.) - defaults to 'UK'
            model: Optional model to use (defaults to DEFAULT_LLM_MODEL)
            use_fallback: Whether to use fallback model on failure (default: True)
            document_version_id: Optional document version ID for logging (not used by internal client)
            
        Returns:
            Dict with 'success', 'content', 'usage', 'model', 'processing_time_ms', etc.
            
        Raises:
            LLMRateLimitError: Rate limit exceeded
            LLMTimeoutError: Request timeout
            LLMServiceUnavailableError: Service unavailable
            LLMAPIKeyError: Invalid API key
            LLMInvalidResponseError: Other API errors
        """
        try:
            if document_version_id:
                logger.debug(f"External LLM request for document version: {document_version_id}, jurisdiction: {jurisdiction}")
            else:
                logger.debug(f"External LLM request for jurisdiction: {jurisdiction}")
            
            # Call internal client with correct parameters
            return self._internal_client.extract_rules(
                extracted_text=extracted_text,
                jurisdiction=jurisdiction,
                model=model,
                use_fallback=use_fallback
            )
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError, 
                LLMAPIKeyError, LLMInvalidResponseError) as e:
            # Re-raise LLM-specific exceptions
            logger.error(f"LLM request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM request: {e}", exc_info=True)
            raise LLMInvalidResponseError(f"Unexpected error: {str(e)}")
