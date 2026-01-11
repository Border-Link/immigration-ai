"""
Adyen Webhook Handler

Handles webhook events from Adyen payment gateway.
"""
from .base import BaseWebhookAPI


class AdyenWebhookAPI(BaseWebhookAPI):
    """Adyen webhook handler."""
    provider_name = 'adyen'
    
    def _extract_signature(self, request) -> str:
        """Extract Adyen-specific signature from headers."""
        return (
            request.headers.get('adyen-signature') or
            request.headers.get('ADYEN-SIGNATURE') or
            request.headers.get('x-adyen-signature') or
            request.headers.get('X-ADYEN-SIGNATURE')
        )
