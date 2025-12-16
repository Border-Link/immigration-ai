import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class UserDeviceSession(models.Model):
    """
    Tracks a user device/session for multi-cookie auth.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="device_sessions"
    )
    session_id = models.CharField(max_length=128, unique=True)  # cookie value for session tracking
    fingerprint = models.CharField(max_length=256, blank=True)  # hashed IP + user-agent
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_mfa_verified = models.BooleanField(default=False)
    last_active = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    device_info = models.JSONField(default=dict, blank=True)


    class Meta:
        db_table = "user_device_sessions"
        indexes = [
            models.Index(fields=["user", "revoked"]),
        ]

    def is_revoked(self):
        return not self.revoked

    def revoke(self):
        self.revoked_at = timezone.now()
        self.revoked = True
        self.save(update_fields=["revoked_at", "revoked"])

    def mark_active(self):
        self.last_active = timezone.now()
        self.save(update_fields=["last_active"])

    def __str__(self):
        return f"DeviceSession(user={self.user.email}, session_id={self.session_id})"
