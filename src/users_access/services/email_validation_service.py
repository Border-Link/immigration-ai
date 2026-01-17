import logging
from django.conf import settings

logger = logging.getLogger('django')


class EmailValidationService:
    """
    Email validation service.
    Only performs deliverability checks in production.
    """

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email deliverability in production only.
        Returns a normalized email or raises ValueError.
        """
        if getattr(settings, "APP_ENV", "local") != "production":
            return email

        try:
            from email_validator import validate_email, EmailNotValidError
        except Exception as exc:
            logger.error(f"Email validation dependency missing: {exc}")
            raise ValueError("Email validation is not configured.")

        try:
            result = validate_email(email, check_deliverability=True)
            return result.email
        except EmailNotValidError as exc:
            raise ValueError(str(exc))
