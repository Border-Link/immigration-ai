"""
Payment Retry Service

Handles automatic retry logic for failed payments.
"""
import logging
from typing import Optional
from decimal import Decimal
from django.utils import timezone
from payments.models.payment import Payment
from payments.selectors.payment_selector import PaymentSelector
from payments.services.payment_service import PaymentService
from payments.services.payment_gateway_service import PaymentGatewayService
from payments.services.payment_history_service import PaymentHistoryService
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError

logger = logging.getLogger('django')


class PaymentRetryService:
    """Service for payment retry logic."""
    
    @staticmethod
    def can_retry(payment: Payment) -> bool:
        """
        Check if a payment can be retried.
        
        Args:
            payment: Payment instance
            
        Returns:
            True if payment can be retried, False otherwise
        """
        if payment.status != 'failed':
            return False
        
        if payment.retry_count >= payment.max_retries:
            return False
        
        return True
    
    @staticmethod
    def retry_payment(payment_id: str) -> Optional[dict]:
        """
        Retry a failed payment.
        
        Args:
            payment_id: UUID of the payment
            
        Returns:
            Dict with retry result or None on error
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for retry")
                return None
            
            if not PaymentRetryService.can_retry(payment):
                logger.warning(f"Payment {payment_id} cannot be retried (status: {payment.status}, retries: {payment.retry_count}/{payment.max_retries})")
                return {
                    'success': False,
                    'error': 'Payment cannot be retried',
                    'reason': 'max_retries_reached' if payment.retry_count >= payment.max_retries else 'invalid_status'
                }
            
            # Update retry count
            payment.retry_count += 1
            payment.last_retry_at = timezone.now()
            payment.status = 'pending'  # Reset to pending for retry
            payment.save()
            
            # Create history entry
            PaymentHistoryService.create_history_entry(
                payment=payment,
                event_type='retry_attempted',
                message=f"Payment retry attempt {payment.retry_count}/{payment.max_retries}",
                previous_status='failed',
                new_status='pending',
                metadata={
                    'retry_count': payment.retry_count,
                    'max_retries': payment.max_retries
                }
            )
            
            # Re-initiate payment with gateway
            if payment.payment_provider:
                try:
                    result = PaymentGatewayService.initialize_payment(
                        payment=payment,
                        return_url=None,  # Will be set by frontend
                        callback_url=None
                    )
                    
                    if result.get('success'):
                        # Update payment with transaction ID
                        if result.get('transaction_id'):
                            PaymentService.update_payment(
                                payment_id=str(payment.id),
                                provider_transaction_id=result.get('transaction_id'),
                                status='processing',
                                changed_by=None,
                                reason=f"Retry attempt {payment.retry_count}"
                            )
                        
                        return {
                            'success': True,
                            'retry_count': payment.retry_count,
                            'payment_url': result.get('payment_url'),
                            'transaction_id': result.get('transaction_id'),
                        }
                    else:
                        # Retry failed
                        PaymentService.update_payment(
                            payment_id=str(payment.id),
                            status='failed',
                            changed_by=None,
                            reason=f"Retry attempt {payment.retry_count} failed: {result.get('error')}"
                        )
                        return {
                            'success': False,
                            'error': result.get('error', 'Failed to initialize payment'),
                            'retry_count': payment.retry_count,
                        }
                        
                except PaymentGatewayError as e:
                    logger.error(f"Payment gateway error during retry for {payment_id}: {e}", exc_info=True)
                    PaymentService.update_payment(
                        payment_id=str(payment.id),
                        status='failed',
                        changed_by=None,
                        reason=f"Retry attempt {payment.retry_count} failed: {str(e)}"
                    )
                    return {
                        'success': False,
                        'error': str(e),
                        'retry_count': payment.retry_count,
                    }
            else:
                # No payment provider, just reset status
                return {
                    'success': True,
                    'retry_count': payment.retry_count,
                    'message': 'Payment status reset to pending (no gateway configured)',
                }
            
        except Exception as e:
            logger.error(f"Error retrying payment {payment_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_retryable_payments() -> list:
        """
        Get all payments that can be retried.
        
        Returns:
            List of Payment instances that can be retried
        """
        try:
            failed_payments = PaymentSelector.get_by_status('failed')
            retryable = []
            
            for payment in failed_payments:
                if PaymentRetryService.can_retry(payment):
                    retryable.append(payment)
            
            return retryable
            
        except Exception as e:
            logger.error(f"Error fetching retryable payments: {e}", exc_info=True)
            return []
