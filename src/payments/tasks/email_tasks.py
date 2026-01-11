"""
Payment Email Tasks

Celery tasks for sending payment-related emails.
"""
from celery import shared_task
import logging
from main_system.utils.tasks_base import BaseTaskWithMeta
from emails.send import SendEmailService
from payments.selectors.payment_selector import PaymentSelector
from users_access.selectors.user_selector import UserSelector
from users_access.selectors.user_profile_selector import UserProfileSelector

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_payment_status_email_task(
    self,
    payment_id: str,
    notification_type: str,
    previous_status: str = None,
    new_status: str = None
):
    """Send email notification for payment status change."""
    try:
        payment = PaymentSelector.get_by_id(payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found for email")
            return
        
        user = payment.case.user
        if not user:
            logger.error(f"User not found for payment {payment_id}")
            return
        
        try:
            profile = UserProfileSelector.get_by_user(user)
            first_name = profile.first_name if profile and profile.first_name else user.email.split('@')[0]
        except Exception:
            first_name = user.email.split('@')[0]
        
        # Determine email content based on notification type
        if notification_type == 'payment_completed':
            subject = "Payment Completed Successfully"
            template = 'payment_completed'
            context = {
                'first_name': first_name,
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
            }
        elif notification_type == 'payment_failed':
            subject = "Payment Failed"
            template = 'payment_failed'
            context = {
                'first_name': first_name,
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'retry_count': payment.retry_count,
                'max_retries': payment.max_retries,
            }
        elif notification_type == 'payment_refunded':
            subject = "Payment Refunded"
            template = 'payment_refunded'
            context = {
                'first_name': first_name,
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'currency': payment.currency,
            }
        else:
            # Generic status change
            subject = f"Payment Status Update: {new_status.title()}"
            template = 'payment_status_update'
            context = {
                'first_name': first_name,
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'currency': payment.currency,
                'previous_status': previous_status,
                'new_status': new_status,
                'status': payment.status,
            }
        
        # Send email
        SendEmailService.send_email(
            to_email=user.email,
            subject=subject,
            template=template,
            context=context
        )
        
        logger.info(f"Payment status email sent to {user.email} for payment {payment_id}")
        
    except Exception as e:
        logger.error(f"Error sending payment status email for {payment_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)
