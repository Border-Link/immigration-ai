from django.db import models
import uuid
from django.conf import settings


class UserSetting(models.Model):
    """
    User Settings model - User preferences and notification settings.
    Immigration-specific settings for case updates, eligibility results, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_settings',
        db_index=True
    )

    # Security Settings
    two_factor_auth = models.BooleanField(default=False, db_index=True)
    totp_secret = models.CharField(max_length=50, null=True, blank=True)

    # Notification Channels (Global Toggles)
    email_notifications = models.BooleanField(default=True, db_index=True)
    sms_notifications = models.BooleanField(default=True, db_index=True)
    push_notifications = models.BooleanField(default=True, db_index=True)

    # Immigration-Specific Notification Preferences
    # Case & Eligibility Notifications
    notify_case_status_updates = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify when case status changes (evaluated, reviewed, etc.)"
    )
    notify_eligibility_results = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify when eligibility check results are ready"
    )
    notify_document_status = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify when documents are verified, rejected, or need attention"
    )
    notify_missing_documents = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify about missing required documents"
    )
    notify_rule_changes = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify when immigration rules change for user's visa type"
    )
    notify_review_updates = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify when human review is assigned or completed"
    )

    # Reviewer-Specific Settings (only relevant for reviewer role)
    notify_review_assignments = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify when new review is assigned (for reviewers)"
    )
    notify_sla_deadlines = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify about approaching SLA deadlines (for reviewers)"
    )
    notify_rule_validation_tasks = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Notify about new rule validation tasks (for reviewers/admins)"
    )

    # UI Preferences
    dark_mode = models.BooleanField(default=False, db_index=True)
    language = models.CharField(
        max_length=10,
        default='en',
        db_index=True,
        help_text="Preferred language code (e.g., 'en', 'fr', 'es')"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's timezone (e.g., 'America/New_York', 'Europe/London')"
    )

    # Privacy & Data Settings
    data_sharing_consent = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Consent for anonymized data sharing for analytics"
    )
    marketing_emails = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Consent to receive marketing/promotional emails"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_settings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email_notifications']),
            models.Index(fields=['notify_case_status_updates']),
            models.Index(fields=['notify_eligibility_results']),
        ]

    def __str__(self):
        return f"Settings for {self.user.email}"