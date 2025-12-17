import uuid
from django.db import models
from django.conf import settings


class OTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_otp',
        db_index=True
    )

    otp = models.CharField(max_length=6, null=True)
    endpoint_token = models.CharField(max_length=255, null=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    type = models.CharField(max_length=100, db_index=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'otps'
        indexes = [
            models.Index(fields=['user', 'otp']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} - {'Verified' if self.is_verified else 'Pending'}"


# Import managers after OTP class definition to avoid circular imports
from users_access.repositories.otp_repository import OTPRepository
from users_access.selectors.otp_selector import OTPSelector

# Assign managers to OTP model
OTP.add_to_class('repository', OTPRepository())
OTP.add_to_class('selector', OTPSelector())
