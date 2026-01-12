"""
Signals for CallSession model.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ai_calls.models.call_session import CallSession
from django.core.cache import cache


@receiver(post_save, sender=CallSession)
def invalidate_call_session_cache(sender, instance, **kwargs):
    """Invalidate cache when call session is saved."""
    cache.delete(f"call_session:{instance.id}")
    cache.delete(f"call_session:case:{instance.case_id}:active")
    cache.delete(f"call_sessions:user:{instance.user_id}")


@receiver(post_delete, sender=CallSession)
def invalidate_call_session_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when call session is deleted."""
    cache.delete(f"call_session:{instance.id}")
    cache.delete(f"call_session:case:{instance.case_id}:active")
    cache.delete(f"call_sessions:user:{instance.user_id}")
