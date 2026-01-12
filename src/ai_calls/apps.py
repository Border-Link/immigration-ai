from django.apps import AppConfig


class AiCallsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_calls"

    def ready(self):
        from .signals import call_session_signals
