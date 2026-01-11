"""
Payment Tasks

Celery tasks for payment operations:
- Status polling
- Automatic retries
- Notifications
"""
from celery import shared_task
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from datetime import timedelta
from main_system.utils.tasks_base import BaseTaskWithMeta
from payments.selectors.payment_selector import PaymentSelector
from payments.services.payment_service import PaymentService
from payments.services.payment_retry_service import PaymentRetryService
from payments.services.payment_notification_service import PaymentNotificationService
from payments.tasks.email_tasks import send_payment_status_email_task

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def poll_payment_status_task(self, payment_id: str) -> Dict[str, Any]:
    """
    Celery task to poll payment gateway for payment status.
    
    This task verifies payment status with the gateway and updates
    the payment record if status has changed.
    
    Args:
        payment_id: UUID of the payment to poll
        
    Returns:
        Dict with polling results
    """
    try:
        logger.info(f"Polling payment status for payment: {payment_id}")
        
        payment = PaymentSelector.get_by_id(payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found for polling")
            return {'success': False, 'error': 'Payment not found'}
        
        # Only poll pending or processing payments
        if payment.status not in ['pending', 'processing']:
            logger.info(f"Payment {payment_id} status is {payment.status}, skipping poll")
            return {'success': True, 'status': payment.status, 'skipped': True}
        
        # Verify payment status with gateway
        result = PaymentService.verify_payment_status(payment_id)
        
        if not result:
            logger.warning(f"Failed to verify payment {payment_id} status")
            return {'success': False, 'error': 'Verification failed'}
        
        # Status was updated by verify_payment_status if changed
        updated_payment = PaymentSelector.get_by_id(payment_id)
        
        return {
            'success': True,
            'payment_id': payment_id,
            'previous_status': payment.status,
            'current_status': updated_payment.status if updated_payment else payment.status,
            'verified': result,
        }
        
    except Exception as e:
        logger.error(f"Error polling payment status for {payment_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def poll_pending_payments_task(self) -> Dict[str, Any]:
    """
    Celery task to poll all pending/processing payments.
    
    This task finds all payments in pending or processing status
    and polls their status with the payment gateway.
    
    Returns:
        Dict with polling results summary
    """
    try:
        logger.info("Starting batch payment status polling")
        
        # Get pending and processing payments
        pending_payments = PaymentSelector.get_by_status('pending')
        processing_payments = PaymentSelector.get_by_status('processing')
        
        all_payments = list(pending_payments) + list(processing_payments)
        
        # Filter to payments with provider and transaction ID
        payments_to_poll = [
            p for p in all_payments
            if p.payment_provider and p.provider_transaction_id
        ]
        
        # Limit to payments created in last 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        payments_to_poll = [
            p for p in payments_to_poll
            if p.created_at >= cutoff_date
        ]
        
        logger.info(f"Polling {len(payments_to_poll)} payments")
        
        results = {
            'total': len(payments_to_poll),
            'success': 0,
            'failed': 0,
            'status_changed': 0,
        }
        
        for payment in payments_to_poll:
            try:
                result = poll_payment_status_task.delay(str(payment.id))
                # Note: In production, you might want to wait for results or use a callback
                results['success'] += 1
            except Exception as e:
                logger.error(f"Error queuing poll task for payment {payment.id}: {e}")
                results['failed'] += 1
        
        logger.info(f"Batch payment polling completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in batch payment polling: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def retry_failed_payments_task(self) -> Dict[str, Any]:
    """
    Celery task to automatically retry failed payments.
    
    This task finds all failed payments that can be retried
    and attempts to retry them.
    
    Returns:
        Dict with retry results summary
    """
    try:
        logger.info("Starting automatic payment retry")
        
        retryable_payments = PaymentRetryService.get_retryable_payments()
        
        logger.info(f"Found {len(retryable_payments)} payments to retry")
        
        results = {
            'total': len(retryable_payments),
            'success': 0,
            'failed': 0,
            'skipped': 0,
        }
        
        for payment in retryable_payments:
            try:
                result = PaymentRetryService.retry_payment(str(payment.id))
                
                if result and result.get('success'):
                    results['success'] += 1
                    logger.info(f"Successfully retried payment {payment.id}")
                else:
                    results['failed'] += 1
                    logger.warning(f"Failed to retry payment {payment.id}: {result.get('error') if result else 'Unknown error'}")
                    
            except Exception as e:
                logger.error(f"Error retrying payment {payment.id}: {e}", exc_info=True)
                results['failed'] += 1
        
        logger.info(f"Automatic payment retry completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in automatic payment retry: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_payment_notification_task(
    self,
    payment_id: str,
    notification_type: str,
    previous_status: str = None,
    new_status: str = None
) -> Dict[str, Any]:
    """
    Celery task to send payment notifications.
    
    Args:
        payment_id: UUID of the payment
        notification_type: Type of notification (status_changed, payment_completed, etc.)
        previous_status: Previous payment status
        new_status: New payment status
        
    Returns:
        Dict with notification results
    """
    try:
        logger.info(f"Sending payment notification for payment {payment_id}")
        
        result = PaymentNotificationService.send_notification(
            payment_id=payment_id,
            notification_type=notification_type,
            previous_status=previous_status,
            new_status=new_status
        )
        
        return {
            'success': result is not None,
            'payment_id': payment_id,
            'notification_type': notification_type,
        }
        
    except Exception as e:
        logger.error(f"Error sending payment notification for {payment_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)
