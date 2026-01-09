"""
LLM client wrapper with retry logic, timeout, rate limiting, and circuit breaker.

This module provides a production-ready wrapper around the OpenAI client
with comprehensive error handling and resilience patterns.
"""

import logging
import time
from typing import Dict, Optional, Any
from django.conf import settings
from openai import OpenAI, RateLimitError, APIError, APIConnectionError, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    before_sleep_log,
    after_log
)
from pybreaker import CircuitBreaker
from data_ingestion.exceptions.rule_parsing_exceptions import (
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceUnavailableError,
    LLMAPIKeyError,
    LLMInvalidResponseError
)
from data_ingestion.helpers.rule_parsing_constants import (
    DEFAULT_LLM_MODEL,
    FALLBACK_LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_SECONDS,
)
from data_ingestion.helpers.rate_limiter import get_rate_limiter

logger = logging.getLogger('django')

# Circuit breaker for LLM calls
# Opens after 5 consecutive failures, resets after 60 seconds
llm_circuit_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    expected_exception=Exception
)


def _is_retryable_error(exception: Exception) -> bool:
    """Check if an exception is retryable."""
    if isinstance(exception, (RateLimitError, APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exception, APIError):
        # Check status code for retryable errors
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
            # 429 (rate limit), 500, 502, 503, 504 are retryable
            return status_code in [429, 500, 502, 503, 504]
    return False


def _classify_openai_error(exception: Exception) -> Exception:
    """Classify OpenAI exceptions into custom exception types."""
    if isinstance(exception, RateLimitError):
        return LLMRateLimitError(f"Rate limit exceeded: {str(exception)}")
    elif isinstance(exception, APITimeoutError):
        return LLMTimeoutError(f"Request timeout: {str(exception)}")
    elif isinstance(exception, APIConnectionError):
        return LLMServiceUnavailableError(f"Service unavailable: {str(exception)}")
    elif isinstance(exception, APIError):
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
            if status_code == 401:
                return LLMAPIKeyError(f"Invalid API key: {str(exception)}")
            elif status_code in [500, 502, 503, 504]:
                return LLMServiceUnavailableError(f"Service error {status_code}: {str(exception)}")
    return LLMInvalidResponseError(f"API error: {str(exception)}")


@llm_circuit_breaker
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(_is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO),
    reraise=True
)
def _call_llm_with_retry(
    client: OpenAI,
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
    response_format: Optional[Dict] = None,
    timeout: float = LLM_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Call LLM API with retry logic and error handling.
    
    Args:
        client: OpenAI client instance
        model: Model name to use
        messages: List of message dicts
        temperature: Temperature setting
        max_tokens: Maximum tokens
        response_format: Optional response format dict
        timeout: Request timeout in seconds
        
    Returns:
        Response dict with 'content' and 'usage' keys
        
    Raises:
        LLMRateLimitError: Rate limit exceeded
        LLMTimeoutError: Request timeout
        LLMServiceUnavailableError: Service unavailable
        LLMAPIKeyError: Invalid API key
        LLMInvalidResponseError: Other API errors
    """
    try:
        start_time = time.time()
        
        # Prepare request parameters
        request_params = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'timeout': timeout
        }
        
        if response_format:
            request_params['response_format'] = response_format
        
        # Make API call
        response = client.chat.completions.create(**request_params)  # type: ignore
        
        processing_time = int((time.time() - start_time) * 1000)  # Convert to ms
        
        # Extract response
        content = response.choices[0].message.content
        usage = response.usage
        
        return {
            'content': content,
            'usage': {
                'prompt_tokens': usage.prompt_tokens if usage else 0,
                'completion_tokens': usage.completion_tokens if usage else 0,
                'total_tokens': usage.total_tokens if usage else 0
            },
            'model': model,
            'processing_time_ms': processing_time
        }
        
    except (RateLimitError, APIConnectionError, APITimeoutError, APIError) as e:
        # Re-raise as custom exception for proper classification
        raise _classify_openai_error(e)
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {e}", exc_info=True)
        raise LLMInvalidResponseError(f"Unexpected error: {str(e)}")


class LLMClient:
    """
    Production-ready LLM client with retry, timeout, rate limiting, and circuit breaker.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = LLM_TIMEOUT_SECONDS):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', None)
        if not self.api_key:
            raise LLMAPIKeyError("OPENAI_API_KEY not set in settings")
        
        self.timeout = timeout
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=timeout,
            max_retries=0  # We handle retries ourselves with tenacity
        )
    
    def extract_rules(
        self,
        extracted_text: str,
        jurisdiction: str = 'UK',
        model: Optional[str] = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Extract rules from text using LLM.
        
        Args:
            extracted_text: Text to extract rules from
            jurisdiction: Jurisdiction code
            model: Model to use (defaults to DEFAULT_LLM_MODEL)
            use_fallback: Whether to use fallback model on failure
            
        Returns:
            Dict with 'success', 'content', 'usage', 'model', 'processing_time_ms'
            
        Raises:
            LLMAPIKeyError: Invalid or missing API key
            LLMRateLimitError: Rate limit exceeded
            LLMTimeoutError: Request timeout
            LLMServiceUnavailableError: Service unavailable
            LLMInvalidResponseError: Other errors
        """
        from data_ingestion.helpers.prompts import (
            get_rule_extraction_system_message,
            get_rule_extraction_user_prompt,
            get_jurisdiction_name
        )
        from data_ingestion.helpers.rule_parsing_constants import MAX_TEXT_LENGTH
        
        # Truncate text if needed
        truncated_text = extracted_text[:MAX_TEXT_LENGTH]
        if len(extracted_text) > MAX_TEXT_LENGTH:
            logger.warning(f"Text truncated from {len(extracted_text)} to {MAX_TEXT_LENGTH} characters")
        
        # Get prompts
        jurisdiction_name = get_jurisdiction_name(jurisdiction)
        system_message = get_rule_extraction_system_message(jurisdiction_name)
        user_prompt = get_rule_extraction_user_prompt(
            jurisdiction_name=jurisdiction_name,
            jurisdiction=jurisdiction,
            extracted_text=truncated_text
        )
        
        messages = [
            {"role": "system", "content": str(system_message)},
            {"role": "user", "content": str(user_prompt)}
        ]
        
        # Estimate tokens (rough: ~4 chars per token)
        estimated_tokens = len(str(system_message) + str(user_prompt)) // 4 + LLM_MAX_TOKENS
        
        # Apply rate limiting
        rate_limiter = get_rate_limiter()
        wait_time = rate_limiter.wait_if_needed(estimated_tokens=estimated_tokens)
        if wait_time > 0:
            logger.info(f"Rate limiter: waited {wait_time:.2f}s before API call")
        
        # Try primary model first
        primary_model = model or DEFAULT_LLM_MODEL
        
        try:
            logger.info(f"Calling LLM for rule extraction (model: {primary_model}, text length: {len(truncated_text)} chars)")
            
            response = _call_llm_with_retry(
                client=self.client,
                model=primary_model,
                messages=messages,  # type: ignore
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"},  # type: ignore
                timeout=self.timeout
            )
            
            # Record actual token usage
            actual_tokens = response.get('usage', {}).get('total_tokens', 0)
            if actual_tokens > 0:
                rate_limiter.record_usage(actual_tokens)
            
            response['success'] = True
            return response
            
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError) as e:
            # Retryable errors - try fallback if enabled
            if use_fallback and primary_model != FALLBACK_LLM_MODEL:
                logger.warning(f"Primary model {primary_model} failed: {e}. Trying fallback {FALLBACK_LLM_MODEL}")
                try:
                    # Apply rate limiting for fallback too
                    wait_time = rate_limiter.wait_if_needed(estimated_tokens=estimated_tokens)
                    if wait_time > 0:
                        logger.info(f"Rate limiter: waited {wait_time:.2f}s before fallback API call")
                    
                    response = _call_llm_with_retry(
                        client=self.client,
                        model=FALLBACK_LLM_MODEL,
                        messages=messages,  # type: ignore
                        temperature=LLM_TEMPERATURE,
                        max_tokens=LLM_MAX_TOKENS,
                        timeout=self.timeout
                    )
                    
                    # Record actual token usage
                    actual_tokens = response.get('usage', {}).get('total_tokens', 0)
                    if actual_tokens > 0:
                        rate_limiter.record_usage(actual_tokens)
                    
                    response['success'] = True
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    raise e  # Re-raise original error
            
            raise
        except LLMAPIKeyError:
            # Don't retry API key errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rule extraction: {e}", exc_info=True)
            raise LLMInvalidResponseError(f"Unexpected error: {str(e)}")
