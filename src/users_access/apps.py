from django.apps import AppConfig


class UsersAccessConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users_access"

    def ready(self):
        from .tasks import otp_tasks
        from .signals import user_settings
        from .signals import user_profile
