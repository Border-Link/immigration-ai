"""
PayPal Payment Gateway Implementation

Implements PayPal payment gateway integration.
"""
import logging
import hmac
import hashlib
import base64
from typing import Dict, Optional, Any
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import requests
from payments.gateways.base import BasePaymentGateway
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

logger = logging.getLogger('django')


class PayPalGateway(BasePaymentGateway):
    """
    PayPal payment gateway implementation.
    
    Requires settings:
    - PAYPAL_CLIENT_ID: PayPal client ID
    - PAYPAL_CLIENT_SECRET: PayPal client secret
    - PAYPAL_MODE: 'sandbox' or 'live' (default: 'sandbox')
    - PAYPAL_WEBHOOK_ID: PayPal webhook ID for signature verification
    """
    
    SANDBOX_BASE_URL = "https://api.sandbox.paypal.com"
    LIVE_BASE_URL = "https://api.paypal.com"
    
    def __init__(self):
        """Initialize PayPal gateway."""
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', None)
        self.mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')
        self.webhook_id = getattr(settings, 'PAYPAL_WEBHOOK_ID', None)
        
        self.base_url = self.SANDBOX_BASE_URL if self.mode == 'sandbox' else self.LIVE_BASE_URL
        self.access_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not configured")
    
    def is_configured(self) -> bool:
        """Check if PayPal is properly configured."""
        return bool(self.client_id and self.client_secret)
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'paypal'
    
    def _get_access_token(self) -> str:
        """
        Get PayPal access token (with caching).
        
        Returns:
            Access token string
            
        Raises:
            PaymentGatewayAuthenticationError: If authentication fails
        """
        # Return cached token if still valid
        if self.access_token and self.token_expires_at:
            if timezone.now() < self.token_expires_at:
                return self.access_token
        
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    'Authorization': f'Basic {auth_b64}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                data={'grant_type': 'client_credentials'},
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self.token_expires_at = timezone.now() + timezone.timedelta(seconds=expires_in - 60)  # 1 min buffer
            
            return self.access_token
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                raise PaymentGatewayAuthenticationError("PayPal authentication failed")
            raise PaymentGatewayError(f"PayPal token request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to get PayPal access token: {e}", exc_info=True)
            raise PaymentGatewayAuthenticationError(f"Failed to authenticate: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for PayPal API requests."""
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to PayPal API.
        
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
            raise PaymentGatewayConfigurationError("PayPal is not configured")
        
        headers = self._get_headers()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            else:
                raise PaymentGatewayError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            if status_code == 401:
                # Token might be expired, try refreshing
                self.access_token = None
                headers = self._get_headers()
                # Retry once
                try:
                    if method == 'GET':
                        response = requests.get(url, headers=headers, params=data, timeout=30)
                    elif method == 'POST':
                        response = requests.post(url, headers=headers, json=data, timeout=30)
                    response.raise_for_status()
                    return response.json()
                except:
                    raise PaymentGatewayAuthenticationError("PayPal authentication failed")
            elif status_code == 429:
                raise PaymentGatewayRateLimitError("PayPal rate limit exceeded")
            elif status_code in [500, 502, 503, 504]:
                raise PaymentGatewayServiceUnavailableError(f"PayPal service error: {status_code}")
            else:
                error_data = {}
                if e.response:
                    try:
                        error_data = e.response.json()
                    except:
                        pass
                raise PaymentGatewayError(f"PayPal API error: {error_data.get('message', str(e))}")
        except requests.exceptions.Timeout:
            raise PaymentGatewayTimeoutError("PayPal request timeout")
        except requests.exceptions.ConnectionError:
            raise PaymentGatewayNetworkError("PayPal connection error")
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"PayPal API request failed: {e}", exc_info=True)
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
        """Initialize a payment with PayPal (create Order)."""
        try:
            # PayPal amount format
            amount_str = f"{amount:.2f}"
            
            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'reference_id': reference,
                    'amount': {
                        'currency_code': currency.upper(),
                        'value': amount_str,
                    },
                    'description': f'Payment for case: {reference}',
                }],
            }
            
            # Add customer information
            if customer_email:
                order_data['purchase_units'][0]['payee'] = {
                    'email_address': customer_email,
                }
            
            # Add application context for redirect URLs
            if return_url:
                order_data['application_context'] = {
                    'return_url': return_url,
                    'cancel_url': return_url,
                    'brand_name': 'Immigration Intelligence Platform',
                    'user_action': 'PAY_NOW',
                }
            
            # Add metadata
            if metadata:
                order_data['purchase_units'][0]['custom_id'] = str(metadata.get('case_id', reference))
            
            response = self._make_request('POST', '/v2/checkout/orders', order_data)
            
            if not response or 'id' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid response from PayPal")
            
            order_id = response['id']
            status = response.get('status', 'CREATED')
            
            # Get approval URL from links
            approval_url = None
            for link in response.get('links', []):
                if link.get('rel') == 'approve':
                    approval_url = link.get('href')
                    break
            
            return {
                'success': True,
                'payment_url': approval_url,
                'transaction_id': order_id,
                'reference': reference,
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize PayPal payment: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to initialize payment: {str(e)}")
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify payment status with PayPal."""
        try:
            response = self._make_request('GET', f'/v2/checkout/orders/{transaction_id}')
            
            if not response or 'id' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid response from PayPal")
            
            status = response.get('status', 'UNKNOWN')
            
            # Map PayPal status to our status
            status_mapping = {
                'CREATED': 'pending',
                'SAVED': 'pending',
                'APPROVED': 'processing',
                'VOIDED': 'failed',
                'COMPLETED': 'completed',
                'PAYER_ACTION_REQUIRED': 'processing',
            }
            
            payment_status = status_mapping.get(status, 'pending')
            
            # Get amount from purchase units
            amount = Decimal('0')
            currency = 'USD'
            if response.get('purchase_units'):
                purchase_unit = response['purchase_units'][0]
                amount_info = purchase_unit.get('amount', {})
                amount = Decimal(amount_info.get('value', '0'))
                currency = amount_info.get('currency_code', 'USD')
            
            # Get capture/payment info
            paid_at = None
            if status == 'COMPLETED' and response.get('purchase_units'):
                purchase_unit = response['purchase_units'][0]
                if purchase_unit.get('payments', {}).get('captures'):
                    capture = purchase_unit['payments']['captures'][0]
                    if capture.get('create_time'):
                        paid_at = timezone.datetime.fromisoformat(
                            capture['create_time'].replace('Z', '+00:00')
                        )
            
            return {
                'success': True,
                'status': payment_status,
                'amount': amount,
                'currency': currency,
                'transaction_id': transaction_id,
                'reference': purchase_unit.get('reference_id', '') if response.get('purchase_units') else '',
                'paid_at': paid_at,
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify PayPal payment: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to verify payment: {str(e)}")
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process PayPal webhook event."""
        try:
            # Verify webhook signature
            if signature and self.webhook_id:
                if not self._verify_webhook_signature(payload, signature, headers):
                    raise PaymentGatewayAuthenticationError("Invalid webhook signature")
            
            event_type = payload.get('event_type', '')
            resource = payload.get('resource', {})
            
            # Handle different event types
            if event_type == 'PAYMENT.CAPTURE.COMPLETED':
                capture = resource
                transaction_id = capture.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
                if not transaction_id:
                    # Try to get from parent payment
                    transaction_id = capture.get('parent_payment')
                
                amount = Decimal(capture.get('amount', {}).get('value', '0'))
                currency = capture.get('amount', {}).get('currency_code', 'USD')
                
                return {
                    'success': True,
                    'event_type': 'payment.completed',
                    'transaction_id': transaction_id or capture.get('id', ''),
                    'status': 'completed',
                    'reference': capture.get('custom_id', ''),
                    'amount': amount,
                    'currency': currency,
                    'verified': bool(signature and self.webhook_id),
                }
            
            elif event_type == 'PAYMENT.CAPTURE.DENIED':
                capture = resource
                transaction_id = capture.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
                
                return {
                    'success': True,
                    'event_type': 'payment.failed',
                    'transaction_id': transaction_id or capture.get('id', ''),
                    'status': 'failed',
                    'reference': capture.get('custom_id', ''),
                    'amount': Decimal(capture.get('amount', {}).get('value', '0')),
                    'currency': capture.get('amount', {}).get('currency_code', 'USD'),
                    'verified': bool(signature and self.webhook_id),
                }
            
            elif event_type == 'CHECKOUT.ORDER.COMPLETED':
                order = resource
                transaction_id = order.get('id')
                amount = Decimal('0')
                currency = 'USD'
                
                if order.get('purchase_units'):
                    purchase_unit = order['purchase_units'][0]
                    amount_info = purchase_unit.get('amount', {})
                    amount = Decimal(amount_info.get('value', '0'))
                    currency = amount_info.get('currency_code', 'USD')
                
                return {
                    'success': True,
                    'event_type': 'payment.completed',
                    'transaction_id': transaction_id,
                    'status': 'completed',
                    'reference': purchase_unit.get('reference_id', '') if order.get('purchase_units') else '',
                    'amount': amount,
                    'currency': currency,
                    'verified': bool(signature and self.webhook_id),
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
            logger.error(f"Failed to process PayPal webhook: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process webhook: {str(e)}")
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Verify PayPal webhook signature."""
        try:
            import json
            
            # PayPal webhook verification requires calling their API
            # For now, we'll do basic validation
            # In production, you should call PayPal's webhook verification API
            
            if not self.webhook_id:
                return False
            
            # PayPal sends webhook ID in headers
            webhook_id_header = headers.get('paypal-webhook-id') if headers else None
            if webhook_id_header != self.webhook_id:
                return False
            
            # Additional verification can be done by calling PayPal's verification API
            # This is a simplified version
            return True
            
        except Exception as e:
            logger.error(f"PayPal webhook signature verification failed: {e}")
            return False
    
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a refund with PayPal."""
        try:
            # First, get the capture ID from the order
            order = self._make_request('GET', f'/v2/checkout/orders/{transaction_id}')
            
            if not order or 'purchase_units' not in order:
                raise PaymentGatewayValidationError("Order has no purchase units")
            
            purchase_unit = order['purchase_units'][0]
            captures = purchase_unit.get('payments', {}).get('captures', [])
            
            if not captures:
                raise PaymentGatewayValidationError("No captures found for order")
            
            capture_id = captures[0].get('id')
            
            # Create refund
            refund_data = {}
            
            if amount:
                refund_data['amount'] = {
                    'value': f"{amount:.2f}",
                    'currency_code': captures[0].get('amount', {}).get('currency_code', 'USD'),
                }
            
            if reason:
                refund_data['note_to_payer'] = reason
            
            response = self._make_request('POST', f'/v2/payments/captures/{capture_id}/refund', refund_data)
            
            if not response or 'id' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid refund response from PayPal")
            
            return {
                'success': True,
                'refund_id': response['id'],
                'amount': Decimal(response.get('amount', {}).get('value', '0')),
                'status': response.get('status', 'COMPLETED').lower(),
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to process PayPal refund: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
