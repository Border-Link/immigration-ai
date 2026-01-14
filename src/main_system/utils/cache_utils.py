import hashlib
from django.core.cache import cache
from functools import wraps
import inspect
import json

_SENTINEL = object()


# -------------------------
# Namespace helpers
# -------------------------

def get_namespace_version(ns_key: str) -> int:
    """
    Always returns a namespace version.
    Creates it atomically if missing.
    """
    return cache.get_or_set(ns_key, 1)


def bump_namespace(ns_key: str) -> None:
    """
    Atomically bump namespace version.
    Safe across multiple workers.
    """
    if not cache.has_key(ns_key):
        cache.set(ns_key, 1)
    cache.incr(ns_key)


# -------------------------
# Cache decorator
# -------------------------

def cache_result(timeout=3600, keys=None, namespace=None):
    keys = keys or []

    def decorator(func):
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments

            # -------- Namespace --------
            ns_key = namespace(*args, **kwargs) if namespace else None
            version = get_namespace_version(ns_key) if ns_key else 1

            # -------- Identity --------
            self_obj = arguments.get('self')
            class_name = self_obj.__class__.__name__ if self_obj else ''

            user = arguments.get('user')
            user_id = getattr(user, 'id', 'anonymous')

            cache_payload = {
                "namespace": ns_key,
                "class": class_name,
                "function": func.__name__,
                "user_id": str(user_id),
                "version": version,
            }

            for key in keys:
                value = arguments.get(key)
                if isinstance(value, (dict, list)):
                    cache_payload[key] = json.dumps(value, sort_keys=True, default=str)
                else:
                    cache_payload[key] = str(value) if value is not None else 'null'

            raw_key = json.dumps(cache_payload, sort_keys=True)
            cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()

            cache_data = cache.get(cache_key, _SENTINEL)
            if cache_data is not _SENTINEL:
                return cache_data

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def invalidate_cache(namespace_adapter):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            ns_key = namespace_adapter(*args, **kwargs)
            bump_namespace(ns_key)
            return result
        return wrapper
    return decorator