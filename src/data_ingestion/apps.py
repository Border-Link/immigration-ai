from django.apps import AppConfig


class DataIngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "data_ingestion"

    def ready(self):
        from .signals import rule_validation_signals
