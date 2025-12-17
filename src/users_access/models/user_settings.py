from django.db import models
import uuid
from django.conf import settings


class UserSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_settings',
        db_index=True
    )

    two_factor_auth = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=50, null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'user_settings'
        ordering = ['-created_at']


    def __str__(self):
        return f"Settings for {self.user.email}"

