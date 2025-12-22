from typing import Optional, Dict
import requests
import logging

logger = logging.getLogger("django")

class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, endpoint: str, headers: Optional[dict] = None, params: Optional[str] = None):
        """
        Make a GET request and return JSON response.
        Returns None on error (for backward compatibility).
        """
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while making GET request to {endpoint}: {e}")
            return None

    def get_with_details(self, endpoint: str, headers: Optional[dict] = None, 
                        params: Optional[str] = None, timeout: Optional[int] = 30) -> Dict:
        """
        Make a GET request and return detailed response information.
        Useful for ingestion systems that need status codes and error details.
        
        Args:
            endpoint: API endpoint path
            headers: Optional request headers
            params: Optional query parameters
            timeout: Request timeout in seconds (default: 30)
            
        Returns:
            Dict with keys: 'content', 'content_type', 'status_code', 'error'
            - On success: content is JSON string, status_code is 200, error is None
            - On error: content is None, status_code may be set, error contains message
        """
        import json
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                content = response.json()
                return {
                    'content': json.dumps(content, indent=2),
                    'content_type': 'application/json',
                    'status_code': response.status_code,
                    'error': None
                }
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from {endpoint}: {e}")
                return {
                    'content': response.text,
                    'content_type': response.headers.get('Content-Type', 'text/plain'),
                    'status_code': response.status_code,
                    'error': f"JSON decode error: {e}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while making GET request to {endpoint}: {e}")
            status_code = None
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
            return {
                'content': None,
                'content_type': None,
                'status_code': status_code,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error making GET request to {endpoint}: {e}")
            return {
                'content': None,
                'content_type': None,
                'status_code': None,
                'error': str(e)
            }

    def post(self, endpoint, data, headers:Optional[dict] = None):
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while making POST request to {endpoint}: {e}")
            return None

    def put(self, endpoint, data, headers: Optional[dict]=None):
        try:
            response = requests.put(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while making PUT request to {endpoint}: {e}")
            return None

    def delete(self, endpoint, headers=None):
        try:
            response = requests.delete(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while making DELETE request to {endpoint}: {e}")
            return None