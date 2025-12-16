from rest_framework import serializers
from users_access.models.user_settings import UserSetting

class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = [
            "id",
            "two_factor_auth",
            "allow_manual_transactions",
            "email_notifications",
            "sms_notifications",
            "push_notifications",
            "transaction_alerts",
            "low_balance_alerts",
            "min_balance_threshold",
            "bill_reminders",
            "bill_reminder_days_before_due",
            "upcoming_payment_reminders",
            "preferred_reminder_channel",
            "budget_tracking_enabled",
            "budget_alert_threshold",
            "savings_goal_tracking",
            "monthly_savings_target",
            "debt_tracking",
            "investment_tracking",
            "investment_risk_preference",
            "ai_recommendations",
            "spending_report",
            "income_report",
            "budget_report",
            "debt_report",
            "investment_report",
            "report_frequency",
            "dark_mode",
            "default_dashboards_views",
            "tax_reminders_enabled",
            "tax_reminder_frequency",
            "tax_reminder_days_before_due",
            "created_at",
            "user",
        ]

