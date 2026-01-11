"""
PayPal Webhook Handler

Handles webhook events from PayPal payment gateway.
"""
from .base import BaseWebhookAPI


class PayPalWebhookAPI(BaseWebhookAPI):
    """PayPal webhook handler."""
    provider_name = 'paypal'
    
    def _extract_signature(self, request) -> str:
        """Extract PayPal-specific signature from headers."""
        return (
            request.headers.get('paypal-transmission-sig') or
            request.headers.get('PAYPAL-TRANSMISSION-SIG') or
            request.headers.get('x-paypal-signature') or
            request.headers.get('X-PAYPAL-SIGNATURE')
        )
