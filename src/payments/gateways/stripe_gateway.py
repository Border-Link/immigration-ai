"""
Stripe Payment Gateway Implementation

Implements Stripe payment gateway integration.
"""
import logging
import hmac
import hashlib
from typing import Dict, Optional, Any
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from external_services.request.http_client import ExternalHTTPClient
from payments.exceptions.payment_gateway_exceptions import (
    PaymentGatewayError,
    PaymentGatewayConfigurationError,
    PaymentGatewayAuthenticationError,
    PaymentGatewayRateLimitError,
    PaymentGatewayTimeoutError,
    PaymentGatewayServiceUnavailableError,
    PaymentGatewayInvalidResponseError,
    PaymentGatewayValidationError,
    PaymentGatewayNetworkError,
)
from payments.gateways import BasePaymentGateway

logger = logging.getLogger('django')


class StripeGateway(BasePaymentGateway):
    """
    Stripe payment gateway implementation.
    
    Requires settings:
    - STRIPE_SECRET_KEY: Stripe secret key
    - STRIPE_PUBLIC_KEY: Stripe public key (optional, for frontend)
    - STRIPE_WEBHOOK_SECRET: Stripe webhook signing secret
    """
    
    API_BASE_URL = "https://api.stripe.com/v1"
    
    def __init__(self):
        """Initialize Stripe gateway."""
        self.secret_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        self.public_key = getattr(settings, 'STRIPE_PUBLIC_KEY', None)
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        
        if not self.secret_key:
            logger.warning("Stripe secret key not configured")
        
        # Initialize HTTP client
        self.client = ExternalHTTPClient(
            base_url=self.API_BASE_URL,
            default_timeout=30,
            max_retries=3
        )
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(self.secret_key)
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'stripe'
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Stripe API requests."""
        if not self.secret_key:
            raise PaymentGatewayConfigurationError("Stripe secret key not configured")
        
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Stripe API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data as dict
            
        Raises:
            PaymentGatewayError: For gateway errors
        """
        if not self.is_configured():
            raise PaymentGatewayConfigurationError("Stripe is not configured")
        
        headers = self._get_headers()
        
        try:
            import requests
            
            url = f"{self.API_BASE_URL}{endpoint}"
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                # Stripe expects form-encoded data
                response = requests.post(url, headers=headers, data=data, timeout=30)
            else:
                raise PaymentGatewayError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            if status_code == 401:
                raise PaymentGatewayAuthenticationError("Stripe authentication failed")
            elif status_code == 429:
                raise PaymentGatewayRateLimitError("Stripe rate limit exceeded")
            elif status_code in [500, 502, 503, 504]:
                raise PaymentGatewayServiceUnavailableError(f"Stripe service error: {status_code}")
            else:
                raise PaymentGatewayError(f"Stripe API error: {str(e)}")
        except requests.exceptions.Timeout:
            raise PaymentGatewayTimeoutError("Stripe request timeout")
        except requests.exceptions.ConnectionError:
            raise PaymentGatewayNetworkError("Stripe connection error")
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Stripe API request failed: {e}", exc_info=True)
            raise PaymentGatewayNetworkError(f"Network error: {str(e)}")
    
    def initialize_payment(
        self,
        amount: Decimal,
        currency: str,
        reference: str,
        customer_email: str,
        customer_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        return_url: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment with Stripe (create PaymentIntent).
        
        For Stripe, we create a PaymentIntent and return the client_secret
        for frontend integration, or create a Checkout Session for redirect flow.
        """
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Create PaymentIntent
            payment_intent_data = {
                'amount': amount_cents,
                'currency': currency.lower(),
                'metadata': {
                    'reference': reference,
                    'customer_email': customer_email,
                    **(metadata or {})
                }
            }
            
            if customer_name:
                payment_intent_data['metadata']['customer_name'] = customer_name
            
            # Create PaymentIntent
            response = self._make_request('POST', '/payment_intents', payment_intent_data)
            
            if not response or 'id' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid response from Stripe")
            
            payment_intent_id = response['id']
            client_secret = response.get('client_secret')
            
            # For redirect flow, create Checkout Session
            if return_url:
                checkout_data = {
                    'payment_intent': payment_intent_id,
                    'success_url': return_url,
                    'cancel_url': return_url,
                    'customer_email': customer_email,
                    'metadata': {
                        'reference': reference,
                        **(metadata or {})
                    }
                }
                
                checkout_response = self._make_request('POST', '/checkout/sessions', checkout_data)
                
                if checkout_response and 'url' in checkout_response:
                    return {
                        'success': True,
                        'payment_url': checkout_response['url'],
                        'transaction_id': payment_intent_id,
                        'reference': reference,
                        'client_secret': client_secret,  # For frontend integration
                    }
            
            # Return PaymentIntent details for frontend integration
            return {
                'success': True,
                'payment_url': None,  # Frontend will use client_secret
                'transaction_id': payment_intent_id,
                'reference': reference,
                'client_secret': client_secret,
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Stripe payment: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to initialize payment: {str(e)}")
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify payment status with Stripe."""
        try:
            response = self._make_request('GET', f'/payment_intents/{transaction_id}')
            
            if not response or 'id' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid response from Stripe")
            
            status = response.get('status', 'unknown')
            amount = Decimal(response.get('amount', 0)) / 100  # Convert from cents
            currency = response.get('currency', 'usd').upper()
            
            # Map Stripe status to our status
            status_mapping = {
                'requires_payment_method': 'pending',
                'requires_confirmation': 'pending',
                'requires_action': 'processing',
                'processing': 'processing',
                'succeeded': 'completed',
                'canceled': 'failed',
            }
            
            payment_status = status_mapping.get(status, 'pending')
            
            paid_at = None
            if status == 'succeeded':
                # Try to get charge from charges list
                charges = response.get('charges', {})
                if isinstance(charges, dict) and charges.get('data'):
                    charge = charges['data'][0]
                    if charge.get('paid') and charge.get('created'):
                        paid_at = timezone.datetime.fromtimestamp(charge['created'], tz=timezone.utc)
                elif response.get('latest_charge'):
                    # PaymentIntent might have latest_charge reference
                    charge_id = response['latest_charge']
                    # Could fetch charge details here if needed
                    paid_at = timezone.now()  # Use current time as fallback
            
            return {
                'success': True,
                'status': payment_status,
                'amount': amount,
                'currency': currency,
                'transaction_id': transaction_id,
                'reference': response.get('metadata', {}).get('reference', ''),
                'paid_at': paid_at,
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify Stripe payment: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to verify payment: {str(e)}")
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process Stripe webhook event."""
        try:
            # Verify webhook signature
            if signature and self.webhook_secret:
                if not self._verify_webhook_signature(payload, signature, headers):
                    raise PaymentGatewayAuthenticationError("Invalid webhook signature")
            
            event_type = payload.get('type', '')
            event_data = payload.get('data', {}).get('object', {})
            
            # Handle different event types
            if event_type == 'payment_intent.succeeded':
                payment_intent = event_data
                transaction_id = payment_intent.get('id')
                amount = Decimal(payment_intent.get('amount', 0)) / 100
                currency = payment_intent.get('currency', 'usd').upper()
                reference = payment_intent.get('metadata', {}).get('reference', '')
                
                return {
                    'success': True,
                    'event_type': 'payment.completed',
                    'transaction_id': transaction_id,
                    'status': 'completed',
                    'reference': reference,
                    'amount': amount,
                    'currency': currency,
                    'verified': bool(signature and self.webhook_secret),
                }
            
            elif event_type == 'payment_intent.payment_failed':
                payment_intent = event_data
                transaction_id = payment_intent.get('id')
                reference = payment_intent.get('metadata', {}).get('reference', '')
                
                return {
                    'success': True,
                    'event_type': 'payment.failed',
                    'transaction_id': transaction_id,
                    'status': 'failed',
                    'reference': reference,
                    'amount': Decimal(payment_intent.get('amount', 0)) / 100,
                    'currency': payment_intent.get('currency', 'usd').upper(),
                    'verified': bool(signature and self.webhook_secret),
                }
            
            else:
                # Unhandled event type
                return {
                    'success': False,
                    'event_type': event_type,
                    'error': f'Unhandled event type: {event_type}',
                }
                
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to process Stripe webhook: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process webhook: {str(e)}")
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Verify Stripe webhook signature."""
        try:
            import json
            import hmac
            import hashlib
            
            # Stripe sends signature in header: stripe-signature
            if headers:
                signature_header = headers.get('stripe-signature', signature)
            else:
                signature_header = signature
            
            # Parse signature (format: t=timestamp,v1=signature)
            sig_parts = signature_header.split(',')
            timestamp = None
            signatures = []
            
            for part in sig_parts:
                if part.startswith('t='):
                    timestamp = part[2:]
                elif part.startswith('v1='):
                    signatures.append(part[3:])
            
            if not timestamp or not signatures:
                return False
            
            # Create signed payload
            signed_payload = f"{timestamp}.{json.dumps(payload, separators=(',', ':'))}"
            
            # Compute expected signature
            expected_sig = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return any(hmac.compare_digest(expected_sig, sig) for sig in signatures)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a refund with Stripe."""
        try:
            # First, get the charge ID from the payment intent
            payment_intent = self._make_request('GET', f'/payment_intents/{transaction_id}')
            
            if not payment_intent or 'charges' not in payment_intent:
                raise PaymentGatewayValidationError("Payment intent has no charges")
            
            charges = payment_intent.get('charges', {}).get('data', [])
            if not charges:
                raise PaymentGatewayValidationError("No charges found for payment intent")
            
            charge_id = charges[0].get('id')
            
            # Create refund
            refund_data = {
                'charge': charge_id,
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convert to cents
            
            if reason:
                refund_data['reason'] = reason
            
            response = self._make_request('POST', '/refunds', refund_data)
            
            if not response or 'id' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid refund response from Stripe")
            
            return {
                'success': True,
                'refund_id': response['id'],
                'amount': Decimal(response.get('amount', 0)) / 100,
                'status': response.get('status', 'pending'),
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to process Stripe refund: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
