"""
Payment Webhook Service

Business logic layer for webhook operations.
All webhook business logic must live here - no direct ORM access.
"""
import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.core.cache import cache
from payments.models.payment import Payment
from payments.selectors.payment_selector import PaymentSelector
from payments.selectors.payment_webhook_event_selector import PaymentWebhookEventSelector
from payments.repositories.payment_webhook_event_repository import PaymentWebhookEventRepository
from payments.services.payment_service import PaymentService
from payments.services.payment_history_service import PaymentHistoryService
from payments.services.payment_gateway_service import PaymentGatewayService
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError

logger = logging.getLogger('django')


class PaymentWebhookService:
    """Service for Payment Webhook business logic."""
    
    @staticmethod
    def process_webhook(
        provider: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a webhook from a payment gateway.
        
        This method:
        1. Validates the webhook signature
        2. Parses the webhook payload
        3. Checks for duplicate events (idempotency)
        4. Updates payment status if needed
        
        Args:
            provider: Payment provider name (stripe, paypal, adyen)
            payload: Webhook payload from gateway
            signature: Webhook signature for verification
            headers: Request headers
            
        Returns:
            Dict with 'success' boolean and result data or error message
        """
        try:
            # Step 1: Process webhook through gateway service
            # Note: PaymentGatewayService.process_webhook returns a dict with webhook data,
            # not a success/error dict. It raises PaymentGatewayError on failure.
            webhook_result = PaymentGatewayService.process_webhook(
                provider=provider,
                payload=payload,
                signature=signature,
                headers=headers or {}
            )
            
            # Step 2: Update payment from webhook result
            update_result = PaymentWebhookService._update_payment_from_webhook(
                provider=provider,
                webhook_result=webhook_result
            )
            
            if not update_result.get('success'):
                return update_result
            
            return {
                'success': True,
                'message': 'Webhook processed successfully',
                'payment_id': update_result.get('payment_id'),
                'status': update_result.get('status')
            }
            
        except PaymentGatewayError as e:
            logger.error(f"Payment gateway error processing webhook: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal server error'}
    
    @staticmethod
    @transaction.atomic
    def _update_payment_from_webhook(
        provider: str,
        webhook_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update payment status from webhook result with idempotency check.
        
        Args:
            provider: Payment provider name
            webhook_result: Result from gateway.process_webhook()
            
        Returns:
            Dict with 'success' boolean and result data or error message
        """
        try:
            transaction_id = webhook_result.get('transaction_id')
            reference = webhook_result.get('reference')
            new_status = webhook_result.get('status')
            event_type = webhook_result.get('event_type')
            event_id = webhook_result.get('event_id')  # Gateway event ID
            
            if not reference:
                logger.warning(f"No reference in webhook result: {webhook_result}")
                return {'success': False, 'error': 'No payment reference in webhook'}
            
            # Step 1: Check for duplicate webhook (idempotency)
            if event_id:
                existing_event = PaymentWebhookEventSelector.get_by_event_id(event_id)
                if existing_event:
                    logger.info(f"Webhook event {event_id} already processed, skipping")
                    return {
                        'success': True,
                        'message': 'Webhook already processed',
                        'payment_id': str(existing_event.payment.id),
                        'status': existing_event.payment.status
                    }
            
            # Step 2: Find payment by reference (payment ID)
            payment = PaymentSelector.get_by_id(reference)
            if not payment:
                logger.warning(f"Payment not found for reference: {reference}")
                return {'success': False, 'error': f'Payment {reference} not found'}
            
            # Step 3: Store webhook event for idempotency
            if event_id:
                try:
                    PaymentWebhookEventRepository.create_webhook_event(
                        payment=payment,
                        event_id=event_id,
                        provider=provider,
                        event_type=event_type or 'unknown',
                        payload=webhook_result
                    )
                except ValueError as e:
                    # Event already exists (shouldn't happen due to check above, but handle gracefully)
                    logger.warning(f"Webhook event {event_id} already exists: {e}")
            
            # Step 4: Create history entry for webhook
            PaymentHistoryService.create_history_entry(
                payment=payment,
                event_type='webhook_received',
                message=f"Webhook received: {event_type}",
                previous_status=payment.status,
                new_status=new_status,
                metadata={'webhook_result': webhook_result},
            )
            
            # Step 5: Update provider transaction ID if not set
            if transaction_id and not payment.provider_transaction_id:
                PaymentService.update_payment(
                    payment_id=str(payment.id),
                    provider_transaction_id=transaction_id,
                    changed_by=None,
                    reason="Webhook: transaction ID set"
                )
            
            # Step 5.5: Security: Validate payment amount to prevent tampering
            webhook_amount = webhook_result.get('amount')
            if webhook_amount is not None:
                from decimal import Decimal
                try:
                    webhook_amount_decimal = Decimal(str(webhook_amount))
                    payment_amount = payment.amount
                    
                    # Allow small rounding differences (0.01)
                    amount_diff = abs(webhook_amount_decimal - payment_amount)
                    if amount_diff > Decimal('0.01'):
                        logger.error(
                            f"Payment amount mismatch for payment {payment.id}: "
                            f"expected {payment_amount}, received {webhook_amount_decimal}"
                        )
                        return {
                            'success': False,
                            'error': f'Payment amount mismatch: expected {payment_amount}, received {webhook_amount_decimal}'
                        }
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error validating payment amount: {e}")
                    # Continue processing if amount validation fails (defensive)
            
            # Step 6: Update status if changed
            if new_status and payment.status != new_status:
                try:
                    PaymentService.update_payment(
                        payment_id=str(payment.id),
                        status=new_status,
                        changed_by=None,
                        reason=f"Webhook: {event_type}"
                    )
                    logger.info(f"Payment {payment.id} status updated to {new_status} via webhook")
                except Exception as update_error:
                    # Handle version conflicts gracefully
                    error_str = str(update_error).lower()
                    if 'version' in error_str or 'modified by another' in error_str:
                        logger.warning(f"Version conflict updating payment {payment.id} from webhook, will retry on next poll")
                        # Still return success since webhook was processed
                    else:
                        # Re-raise if it's not a version conflict
                        raise
            
            return {
                'success': True,
                'payment_id': str(payment.id),
                'status': new_status or payment.status
            }
            
        except Exception as e:
            logger.error(f"Failed to update payment from webhook: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def check_rate_limit(provider: str, client_ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """
        Check if webhook rate limit is exceeded.
        
        Args:
            provider: Payment provider name
            client_ip: Client IP address
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            
        Returns:
            True if rate limit is exceeded, False otherwise
        """
        cache_key = f"webhook_rate_limit:{provider}:{client_ip}"
        request_count = cache.get(cache_key, 0)
        
        if request_count >= max_requests:
            logger.warning(f"Rate limit exceeded for webhook from {client_ip} (provider: {provider})")
            return True
        
        # Increment counter
        cache.set(cache_key, request_count + 1, timeout=window_seconds)
        return False
