"""
Adyen Payment Gateway Implementation

Implements Adyen payment gateway integration.
"""
import logging
import hmac
import hashlib
import base64
import json
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


class AdyenGateway(BasePaymentGateway):
    """
    Adyen payment gateway implementation.
    
    Requires settings:
    - ADYEN_API_KEY: Adyen API key
    - ADYEN_MERCHANT_ACCOUNT: Adyen merchant account
    - ADYEN_ENVIRONMENT: 'test' or 'live' (default: 'test')
    - ADYEN_HMAC_KEY: Adyen HMAC key for webhook signature verification
    """
    
    TEST_BASE_URL = "https://pal-test.adyen.com"
    LIVE_BASE_URL = "https://pal-live.adyen.com"
    
    def __init__(self):
        """Initialize Adyen gateway."""
        self.api_key = getattr(settings, 'ADYEN_API_KEY', None)
        self.merchant_account = getattr(settings, 'ADYEN_MERCHANT_ACCOUNT', None)
        self.environment = getattr(settings, 'ADYEN_ENVIRONMENT', 'test')
        self.hmac_key = getattr(settings, 'ADYEN_HMAC_KEY', None)
        
        self.base_url = self.TEST_BASE_URL if self.environment == 'test' else self.LIVE_BASE_URL
        
        if not self.api_key or not self.merchant_account:
            logger.warning("Adyen credentials not configured")
    
    def is_configured(self) -> bool:
        """Check if Adyen is properly configured."""
        return bool(self.api_key and self.merchant_account)
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'adyen'
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Adyen API requests."""
        if not self.api_key:
            raise PaymentGatewayConfigurationError("Adyen API key not configured")
        
        return {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Adyen API.
        
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
            raise PaymentGatewayConfigurationError("Adyen is not configured")
        
        headers = self._get_headers()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise PaymentGatewayError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            error_data = {}
            if e.response:
                try:
                    error_data = e.response.json()
                except:
                    pass
            
            if status_code == 401:
                raise PaymentGatewayAuthenticationError("Adyen authentication failed")
            elif status_code == 429:
                raise PaymentGatewayRateLimitError("Adyen rate limit exceeded")
            elif status_code in [500, 502, 503, 504]:
                raise PaymentGatewayServiceUnavailableError(f"Adyen service error: {status_code}")
            else:
                error_message = error_data.get('message', str(e))
                raise PaymentGatewayError(f"Adyen API error: {error_message}")
        except requests.exceptions.Timeout:
            raise PaymentGatewayTimeoutError("Adyen request timeout")
        except requests.exceptions.ConnectionError:
            raise PaymentGatewayNetworkError("Adyen connection error")
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Adyen API request failed: {e}", exc_info=True)
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
        """Initialize a payment with Adyen (create Payment Session)."""
        try:
            # Adyen amount format (in minor units, e.g., cents for USD)
            amount_value = int(amount * 100)
            
            payment_data = {
                'amount': {
                    'value': amount_value,
                    'currency': currency.upper(),
                },
                'reference': reference,
                'merchantAccount': self.merchant_account,
                'returnUrl': return_url or callback_url or '',
                'shopperEmail': customer_email,
            }
            
            if customer_name:
                payment_data['shopperName'] = {
                    'firstName': customer_name.split()[0] if customer_name else '',
                    'lastName': ' '.join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else '',
                }
            
            if metadata:
                payment_data['metadata'] = metadata
            
            # Create payment session
            response = self._make_request('POST', '/v68/paymentSession', payment_data)
            
            if not response or 'paymentSession' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid response from Adyen")
            
            payment_session = response.get('paymentSession')
            
            return {
                'success': True,
                'payment_url': None,  # Adyen uses paymentSession for frontend integration
                'transaction_id': reference,  # Use reference as transaction ID initially
                'reference': reference,
                'payment_session': payment_session,  # For frontend integration
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Adyen payment: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to initialize payment: {str(e)}")
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify payment status with Adyen."""
        try:
            # Adyen uses reference to check payment status
            # We need to search for payments by reference
            search_data = {
                'merchantAccount': self.merchant_account,
                'reference': transaction_id,
            }
            
            response = self._make_request('POST', '/v68/payments/search', search_data)
            
            if not response or 'data' not in response or not response['data']:
                raise PaymentGatewayInvalidResponseError("Payment not found in Adyen")
            
            payment = response['data'][0]
            result_code = payment.get('resultCode', 'UNKNOWN')
            psp_reference = payment.get('pspReference', transaction_id)
            
            # Map Adyen result code to our status
            status_mapping = {
                'Authorised': 'completed',
                'Received': 'processing',
                'Pending': 'processing',
                'Refused': 'failed',
                'Cancelled': 'failed',
                'Error': 'failed',
            }
            
            payment_status = status_mapping.get(result_code, 'pending')
            
            # Get amount
            amount = Decimal('0')
            currency = 'USD'
            if payment.get('amount'):
                amount = Decimal(payment['amount'].get('value', 0)) / 100
                currency = payment['amount'].get('currency', 'USD')
            
            # Get payment date
            paid_at = None
            if payment_status == 'completed' and payment.get('eventDate'):
                paid_at = timezone.datetime.fromisoformat(
                    payment['eventDate'].replace('Z', '+00:00')
                )
            
            return {
                'success': True,
                'status': payment_status,
                'amount': amount,
                'currency': currency,
                'transaction_id': psp_reference,
                'reference': payment.get('merchantReference', transaction_id),
                'paid_at': paid_at,
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify Adyen payment: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to verify payment: {str(e)}")
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process Adyen webhook event."""
        try:
            # Verify webhook signature
            if signature and self.hmac_key:
                if not self._verify_webhook_signature(payload, signature, headers):
                    raise PaymentGatewayAuthenticationError("Invalid webhook signature")
            
            notification_items = payload.get('notificationItems', [])
            if not notification_items:
                return {
                    'success': False,
                    'error': 'No notification items in webhook',
                }
            
            # Process first notification item
            notification = notification_items[0].get('NotificationRequestItem', {})
            event_code = notification.get('eventCode', '')
            success = notification.get('success', 'false').lower() == 'true'
            psp_reference = notification.get('pspReference', '')
            merchant_reference = notification.get('merchantReference', '')
            
            # Get amount
            amount = Decimal('0')
            currency = 'USD'
            if notification.get('amount'):
                amount = Decimal(notification['amount'].get('value', 0)) / 100
                currency = notification['amount'].get('currency', 'USD')
            
            # Map event codes
            if event_code == 'AUTHORISATION' and success:
                return {
                    'success': True,
                    'event_type': 'payment.completed',
                    'transaction_id': psp_reference,
                    'status': 'completed',
                    'reference': merchant_reference,
                    'amount': amount,
                    'currency': currency,
                    'verified': bool(signature and self.hmac_key),
                }
            elif event_code == 'AUTHORISATION' and not success:
                return {
                    'success': True,
                    'event_type': 'payment.failed',
                    'transaction_id': psp_reference,
                    'status': 'failed',
                    'reference': merchant_reference,
                    'amount': amount,
                    'currency': currency,
                    'verified': bool(signature and self.hmac_key),
                }
            elif event_code == 'REFUND':
                return {
                    'success': True,
                    'event_type': 'payment.refunded',
                    'transaction_id': psp_reference,
                    'status': 'refunded',
                    'reference': merchant_reference,
                    'amount': amount,
                    'currency': currency,
                    'verified': bool(signature and self.hmac_key),
                }
            else:
                return {
                    'success': False,
                    'event_type': event_code,
                    'error': f'Unhandled event type: {event_code}',
                }
                
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to process Adyen webhook: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process webhook: {str(e)}")
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Verify Adyen webhook signature using HMAC."""
        try:
            if not self.hmac_key:
                return False
            
            # Adyen sends signature in header: Adyen-Signature
            signature_header = headers.get('adyen-signature') if headers else signature
            if not signature_header:
                return False
            
            # Parse signature (format: key1=value1,key2=value2)
            signature_parts = {}
            for part in signature_header.split(','):
                if '=' in part:
                    key, value = part.split('=', 1)
                    signature_parts[key.strip()] = value.strip()
            
            # Get HMAC signature
            hmac_signature = signature_parts.get('hmacSignature')
            if not hmac_signature:
                return False
            
            # Create data string for verification
            # Adyen uses: merchantReference:originalReference:currencyCode:value:eventCode:success
            notification = payload.get('notificationItems', [{}])[0].get('NotificationRequestItem', {})
            
            merchant_ref = notification.get('merchantReference', '')
            original_ref = notification.get('originalReference', merchant_ref)
            currency_code = notification.get('amount', {}).get('currency', '')
            value = notification.get('amount', {}).get('value', '')
            event_code = notification.get('eventCode', '')
            success = notification.get('success', 'false')
            
            data_string = f"{merchant_ref}:{original_ref}:{currency_code}:{value}:{event_code}:{success}"
            
            # Compute expected HMAC
            expected_hmac = hmac.new(
                self.hmac_key.encode('utf-8'),
                data_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_hmac, hmac_signature)
            
        except Exception as e:
            logger.error(f"Adyen webhook signature verification failed: {e}")
            return False
    
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a refund with Adyen."""
        try:
            refund_data = {
                'merchantAccount': self.merchant_account,
                'originalReference': transaction_id,
            }
            
            if amount:
                refund_data['modificationAmount'] = {
                    'value': int(amount * 100),
                    'currency': 'USD',
                }
            
            if reason:
                refund_data['reference'] = f"Refund: {reason}"
            
            response = self._make_request('POST', f'/v68/payments/{transaction_id}/refunds', refund_data)
            
            if not response or 'pspReference' not in response:
                raise PaymentGatewayInvalidResponseError("Invalid refund response from Adyen")
            
            return {
                'success': True,
                'refund_id': response['pspReference'],
                'amount': amount or Decimal('0'),
                'status': response.get('response', 'received').lower(),
            }
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to process Adyen refund: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
