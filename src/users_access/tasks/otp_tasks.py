from celery import shared_task
import logging
from django.conf import settings
from emails.send import SendEmailService
from main_system.utils.tasks_base import BaseTaskWithMeta

logger = logging.getLogger('django')

OTP_TEMPLATE = "otp/otp_email.html"
OTP_SUBJECT = "Your OTP Code!"


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_otp_email(self, email, first_name, otp):
    try:
        logger.info(f"Sending OTP email to {email}")

        context = build_email_data(email, first_name, otp)

        SendEmailService().send_mail(
            subject=OTP_SUBJECT,
            template_name=OTP_TEMPLATE,
            context=context,
            recipient_list=[email]
        )

        logger.info(f"OTP email sent successfully to {email}")
        return {
            "status": "success",
            "email": email,
            "first_name": first_name,
            "otp": otp
        }

    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {e}")
        raise self.retry(exc=e, countdown=10, max_retries=3)


def build_email_data(email, first_name, otp):
    return {
        "first_name": first_name,
        "email": email,
        "otp": otp,
        "site_name": getattr(settings, 'SITE_NAME', 'Immigration Intelligence Platform'),
    }
