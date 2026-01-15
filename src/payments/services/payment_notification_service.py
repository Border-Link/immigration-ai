"""
Payment Notification Service

Handles email and in-app notifications for payment events.
"""
import logging
from typing import Optional
from payments.models.payment import Payment
from payments.selectors.payment_selector import PaymentSelector
from users_access.services.notification_service import NotificationService

logger = logging.getLogger('django')


class PaymentNotificationService:
    """Service for payment notifications."""
    
    @staticmethod
    def send_notification(
        payment_id: str,
        notification_type: str,
        previous_status: str = None,
        new_status: str = None
    ) -> Optional[bool]:
        """
        Send notification for a payment event.
        
        Args:
            payment_id: UUID of the payment
            notification_type: Type of notification
            previous_status: Previous payment status
            new_status: New payment status
            
        Returns:
            True if notification sent successfully, None on error
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for notification")
                return None
            
            # Pre-case payments may not yet be attached to a case.
            user = payment.user if payment.case_id is None else payment.case.user
            
            # Determine notification details based on type
            if notification_type == 'status_changed':
                title, message, priority = PaymentNotificationService._get_status_change_notification(
                    payment, previous_status, new_status
                )
            elif notification_type == 'payment_completed':
                title = "Payment Completed"
                message = f"Your payment of {payment.amount} {payment.currency} has been completed successfully."
                priority = 'high'
            elif notification_type == 'payment_failed':
                title = "Payment Failed"
                message = f"Your payment of {payment.amount} {payment.currency} has failed. Please try again."
                priority = 'high'
            elif notification_type == 'payment_refunded':
                title = "Payment Refunded"
                message = f"Your payment of {payment.amount} {payment.currency} has been refunded."
                priority = 'medium'
            else:
                title = "Payment Update"
                message = f"Your payment status has been updated."
                priority = 'medium'
            
            # Send in-app notification
            NotificationService.create_notification(
                user_id=str(user.id),
                notification_type='payment_status',
                title=title,
                message=message,
                priority=priority,
                related_entity_type='payment',
                related_entity_id=str(payment.id),
                metadata={
                    'payment_id': str(payment.id),
                    'amount': str(payment.amount),
                    'currency': payment.currency,
                    'status': payment.status,
                    'previous_status': previous_status,
                    'notification_type': notification_type,
                }
            )
            
            # Send email notification (async via Celery)
            # Lazy import to avoid circular dependency
            from payments.tasks.payment_tasks import send_payment_notification_task
            send_payment_notification_task.delay(
                payment_id=str(payment.id),
                notification_type=notification_type,
                previous_status=previous_status,
                new_status=new_status
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending payment notification: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _get_status_change_notification(
        payment: Payment,
        previous_status: str,
        new_status: str
    ) -> tuple:
        """
        Get notification details for status change.
        
        Returns:
            Tuple of (title, message, priority)
        """
        status_messages = {
            'pending': 'Your payment is pending.',
            'processing': 'Your payment is being processed.',
            'completed': 'Your payment has been completed successfully.',
            'failed': 'Your payment has failed. Please try again.',
            'refunded': 'Your payment has been refunded.',
        }
        
        title = f"Payment Status: {new_status.title()}"
        message = status_messages.get(new_status, f'Your payment status has changed from {previous_status} to {new_status}.')
        
        priority = 'high' if new_status in ['completed', 'failed'] else 'medium'
        
        return title, message, priority
