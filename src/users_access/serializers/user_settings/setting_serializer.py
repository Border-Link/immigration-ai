from rest_framework import serializers
from users_access.models.user_settings import UserSetting

class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = [
            "id",
            "two_factor_auth",
            "totp_secret",
            "email_notifications",
            "sms_notifications",
            "push_notifications",
            "notify_case_status_updates",
            "notify_eligibility_results",
            "notify_document_status",
            "notify_missing_documents",
            "notify_rule_changes",
            "notify_review_updates",
            "notify_review_assignments",
            "notify_sla_deadlines",
            "notify_rule_validation_tasks",
            "dark_mode",
            "language",
            "timezone",
            "data_sharing_consent",
            "marketing_emails",
            "updated_at",
            "created_at",
        ]

