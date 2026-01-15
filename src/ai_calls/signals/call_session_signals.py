"""
Signals for CallSession model.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ai_calls.models.call_session import CallSession
from main_system.utils.cache_utils import bump_namespace


def _call_sessions_cache_namespace(*args, **kwargs) -> str:
    return "call_sessions"


@receiver(post_save, sender=CallSession)
def invalidate_call_session_cache(sender, instance, **kwargs):
    """Invalidate cache when call session is saved."""
    bump_namespace(_call_sessions_cache_namespace())


@receiver(post_delete, sender=CallSession)
def invalidate_call_session_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when call session is deleted."""
    bump_namespace(_call_sessions_cache_namespace())
