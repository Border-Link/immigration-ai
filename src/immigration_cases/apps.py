from django.apps import AppConfig


class ImmigrationCasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "immigration_cases"

    def ready(self):
        from .signals import case_signals
