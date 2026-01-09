"""
HTTP client for external HTTP requests.

Provides a centralized, production-ready HTTP client with:
- Retry logic
- Rate limiting
- Error handling
- Request/response logging
- Timeout configuration
"""

import logging
from typing import Optional, Dict, Any
from helpers.request.client import Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests

logger = logging.getLogger('django')


class ExternalHTTPClient:
    """
    Production-ready HTTP client for external API requests.
    
    All external HTTP requests should go through this client to ensure:
    - Consistent error handling
    - Retry logic
    - Rate limiting
    - Request logging
    - Timeout management
    """
    
    def __init__(
        self,
        base_url: str,
        default_timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: bool = True
    ):
        """
        Initialize external HTTP client.
        
        Args:
            base_url: Base URL for all requests
            default_timeout: Default timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff: Whether to use exponential backoff
        """
        self.base_url = base_url.rstrip('/')
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.client = Client(base_url=base_url)
    
    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        return_details: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Make a GET request.
        
        Args:
            endpoint: API endpoint path
            headers: Optional request headers
            params: Optional query parameters
            timeout: Request timeout in seconds (default: self.default_timeout)
            return_details: If True, returns detailed response with status_code, error, etc.
            
        Returns:
            If return_details=False: JSON response or None on error
            If return_details=True: Dict with 'content', 'content_type', 'status_code', 'error'
        """
        timeout = timeout or self.default_timeout
        
        if return_details:
            return self._get_with_details(endpoint, headers, params, timeout)
        else:
            return self._get_with_retry(endpoint, headers, params, timeout)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ))
    )
    def _get_with_retry(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Make GET request with retry logic."""
        try:
            logger.debug(f"GET {self.base_url}{endpoint}")
            return self.client.get(endpoint, headers, params)
        except Exception as e:
            logger.error(f"GET request failed for {endpoint}: {e}")
            raise
    
    def _get_with_details(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make GET request and return detailed response."""
        try:
            logger.debug(f"GET {self.base_url}{endpoint}")
            return self.client.get_with_details(endpoint, headers, params, timeout)
        except Exception as e:
            logger.error(f"GET request failed for {endpoint}: {e}")
            return {
                'content': None,
                'content_type': None,
                'status_code': None,
                'error': str(e)
            }
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make a POST request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            headers: Optional request headers
            timeout: Request timeout in seconds
            
        Returns:
            JSON response or None on error
        """
        timeout = timeout or self.default_timeout
        
        try:
            logger.debug(f"POST {self.base_url}{endpoint}")
            return self._post_with_retry(endpoint, data, headers, timeout)
        except Exception as e:
            logger.error(f"POST request failed for {endpoint}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ))
    )
    def _post_with_retry(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Make POST request with retry logic."""
        try:
            return self.client.post(endpoint, data or {}, headers)
        except Exception as e:
            logger.error(f"POST request failed for {endpoint}: {e}")
            raise
    
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make a PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            headers: Optional request headers
            timeout: Request timeout in seconds
            
        Returns:
            JSON response or None on error
        """
        timeout = timeout or self.default_timeout
        
        try:
            logger.debug(f"PUT {self.base_url}{endpoint}")
            return self._put_with_retry(endpoint, data, headers, timeout)
        except Exception as e:
            logger.error(f"PUT request failed for {endpoint}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ))
    )
    def _put_with_retry(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Make PUT request with retry logic."""
        try:
            return self.client.put(endpoint, data or {}, headers)
        except Exception as e:
            logger.error(f"PUT request failed for {endpoint}: {e}")
            raise
    
    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make a DELETE request.
        
        Args:
            endpoint: API endpoint path
            headers: Optional request headers
            timeout: Request timeout in seconds
            
        Returns:
            JSON response or None on error
        """
        timeout = timeout or self.default_timeout
        
        try:
            logger.debug(f"DELETE {self.base_url}{endpoint}")
            return self._delete_with_retry(endpoint, headers, timeout)
        except Exception as e:
            logger.error(f"DELETE request failed for {endpoint}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ))
    )
    def _delete_with_retry(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Make DELETE request with retry logic."""
        try:
            return self.client.delete(endpoint, headers)
        except Exception as e:
            logger.error(f"DELETE request failed for {endpoint}: {e}")
            raise
