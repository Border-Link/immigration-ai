from django.apps import AppConfig


class AiDecisionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_decisions"

    def ready(self):
        from .signals import eligibility_result_signals
