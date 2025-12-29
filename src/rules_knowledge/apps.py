from django.apps import AppConfig


class RulesKnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rules_knowledge"

    def ready(self):
        """Import signals when app is ready."""
        import rules_knowledge.signals  # noqa
