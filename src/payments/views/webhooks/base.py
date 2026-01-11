"""
Base Webhook Handler

Base class for all payment gateway webhook handlers.
"""
import logging
import json
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from main_system.base.base_api import BaseAPI
from payments.services.payment_webhook_service import PaymentWebhookService
from payments.serializers.webhook.webhook_serializer import WebhookPayloadSerializer
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError

logger = logging.getLogger('django')


@method_decorator(csrf_exempt, name='dispatch')
class BaseWebhookAPI(BaseAPI):
    """
    Base class for webhook handlers.
    
    All webhook endpoints should be CSRF-exempt since they're called by external services.
    Extends BaseAPI to follow system architecture patterns.
    """
    
    provider_name = None
    
    def post(self, request):
        """
        Handle webhook POST request with signature verification and rate limiting.
        
        Follows architecture: View → Service → Selector/Repository
        """
        try:
            # Step 1: Extract client IP for rate limiting
            client_ip = self._get_client_ip(request)
            
            # Step 2: Check rate limit (via service)
            if PaymentWebhookService.check_rate_limit(
                provider=self.get_provider_name(),
                client_ip=client_ip
            ):
                return self.api_response(
                    message='Rate limit exceeded',
                    data=None,
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Step 3: Parse payload
            try:
                if request.content_type == 'application/json':
                    payload = json.loads(request.body)
                else:
                    payload = request.POST.dict()
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid webhook payload from {client_ip}: {e}")
                return self.api_response(
                    message='Invalid payload format',
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Step 4: Validate payload (basic validation, provider-specific happens in service)
            serializer = WebhookPayloadSerializer(data=payload)
            if not serializer.is_valid():
                logger.warning(f"Webhook payload validation failed: {serializer.errors}")
                # Continue anyway - webhook payloads vary by provider
            
            # Step 5: Extract signature
            signature = self._extract_signature(request)
            
            # Step 6: Require signature in production
            if not settings.DEBUG and not signature:
                logger.warning(f"Webhook from {self.get_provider_name()} missing signature in production (IP: {client_ip})")
                return self.api_response(
                    message='Signature required',
                    data=None,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Step 7: Process webhook (via service)
            headers = dict(request.headers)
            result = PaymentWebhookService.process_webhook(
                provider=self.get_provider_name(),
                payload=payload,
                signature=signature,
                headers=headers
            )
            
            # Step 8: Return response
            if not result.get('success'):
                logger.warning(f"Webhook processing returned failure: {result.get('error')}")
                # Return 200 to acknowledge webhook (gateway expects 200 for retries)
                return self.api_response(
                    message=result.get('error', 'Webhook ignored'),
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            
            return self.api_response(
                message='Webhook processed successfully',
                data={
                    'payment_id': result.get('payment_id'),
                    'status': result.get('status')
                },
                status_code=status.HTTP_200_OK
            )
            
        except PaymentGatewayError as e:
            logger.error(f"Payment gateway error in webhook: {e}", exc_info=True)
            return self.api_response(
                message=str(e),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return self.api_response(
                message='Internal server error',
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_provider_name(self) -> str:
        """Get provider name. Must be overridden by child classes."""
        if self.provider_name:
            return self.provider_name
        raise NotImplementedError("Child classes must set provider_name")
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP address from request."""
        return (
            request.META.get('REMOTE_ADDR') or
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or
            'unknown'
        )
    
    def _extract_signature(self, request) -> str:
        """
        Extract webhook signature from request headers.
        
        Child classes can override for provider-specific signature extraction.
        """
        # Default: try common header names
        signature_headers = [
            'x-signature',
            'stripe-signature',
            'paypal-transmission-sig',
            'adyen-signature',
            'signature',
        ]
        
        for header_name in signature_headers:
            signature = request.headers.get(header_name) or request.headers.get(header_name.upper())
            if signature:
                return signature
        
        return None
