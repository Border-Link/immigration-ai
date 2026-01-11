"""
Stripe Webhook Handler

Handles webhook events from Stripe payment gateway.
"""
from .base import BaseWebhookAPI


class StripeWebhookAPI(BaseWebhookAPI):
    """Stripe webhook handler."""
    provider_name = 'stripe'
    
    def _extract_signature(self, request) -> str:
        """Extract Stripe-specific signature from headers."""
        return request.headers.get('stripe-signature') or request.headers.get('STRIPE-SIGNATURE')
