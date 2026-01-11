from django.apps import AppConfig


class DocumentProcessingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_processing'
    verbose_name = 'Document Processing'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import document_processing.signals  # noqa
        except ImportError:
            pass
