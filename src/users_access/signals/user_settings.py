from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from users_access.models.user_settings import UserSetting


User = get_user_model()

@receiver(post_save, sender=User)
def create_user_setting(sender, instance, created, **kwargs):
    if created:
        UserSetting.objects.create_user_setting(user_id=instance.id)
