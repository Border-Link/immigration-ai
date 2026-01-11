import hashlib
from django.core.cache import cache
from functools import wraps
import inspect
import json


def cache_result(timeout=3600, keys=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments

            # Handle instance (self) in key
            self_obj = arguments.get('self')
            class_name = self_obj.__class__.__name__ if self_obj else ''

            user = arguments.get('user')
            user_id = getattr(user, 'id', 'anonymous')

            cache_payload = {
                "class": class_name,
                "function": func.__name__,
                "user_id": str(user_id)
            }

            if keys:
                for key in keys:
                    value = arguments.get(key)
                    if isinstance(value, (dict, list)):
                        cache_payload[key] = json.dumps(value, sort_keys=True, default=str)
                    else:
                        cache_payload[key] = str(value) if value is not None else 'null'

            raw_key = json.dumps(cache_payload, sort_keys=True)
            cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()

            cache_data = cache.get(cache_key)
            if cache_data:
                return cache_data

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
