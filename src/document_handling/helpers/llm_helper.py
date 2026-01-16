"""
LLM Helper for Document Handling

Provides a centralized interface for LLM API calls in document handling.
Uses external_services for consistent error handling and retry logic.
"""
import logging
import json
from typing import Dict, Optional, Any, List
from django.conf import settings
from external_services.request.llm_client import ExternalLLMClient
from data_ingestion.exceptions.rule_parsing_exceptions import (
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceUnavailableError,
    LLMAPIKeyError,
    LLMInvalidResponseError
)

logger = logging.getLogger('django')


def call_llm_for_document_processing(
    system_message: str,
    user_prompt: str,
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    max_tokens: int = 500,
    response_format: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Call LLM API for document processing operations.
    
    This is a generic wrapper that uses the internal LLM client from data_ingestion
    through external_services for consistent error handling.
    
    Args:
        system_message: System message for LLM
        user_prompt: User prompt with task instructions
        model: Model to use (default: gpt-5.2)
        temperature: Temperature setting (default: 0.1 for consistency)
        max_tokens: Maximum tokens in response (default: 500)
        response_format: Optional response format dict (e.g., {"type": "json_object"})
        
    Returns:
        Dict with 'content', 'usage', 'model', 'processing_time_ms', or None on error
        
    Raises:
        LLMRateLimitError: Rate limit exceeded
        LLMTimeoutError: Request timeout
        LLMServiceUnavailableError: Service unavailable
        LLMAPIKeyError: Invalid API key
        LLMInvalidResponseError: Other API errors
    """
    try:
        # Use internal LLM client directly (it has all the retry logic and error handling)
        from data_ingestion.helpers.llm_client import LLMClient, _call_llm_with_retry
        from data_ingestion.helpers.rule_parsing_constants import LLM_TIMEOUT_SECONDS
        
        # Initialize LLM client
        llm_client = LLMClient(timeout=LLM_TIMEOUT_SECONDS)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call LLM with retry logic
        response = _call_llm_with_retry(
            client=llm_client.client,
            model=model,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            timeout=LLM_TIMEOUT_SECONDS
        )
        
        return response
        
    except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError,
            LLMAPIKeyError, LLMInvalidResponseError) as e:
        logger.error(f"LLM call failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {e}", exc_info=True)
        raise LLMInvalidResponseError(f"Unexpected error: {str(e)}")


def parse_llm_json_response(response_content: str) -> Optional[Dict]:
    """
    Parse LLM JSON response, handling markdown code blocks.
    
    Args:
        response_content: Raw response content from LLM
        
    Returns:
        Parsed JSON dict or None if parsing fails
    """
    try:
        # Remove markdown code blocks if present
        content = response_content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        
        # Parse JSON
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response content: {response_content[:500]}")
        return None
    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}", exc_info=True)
        return None
