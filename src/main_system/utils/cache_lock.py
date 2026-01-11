from functools import wraps
import time

def with_lock(lock_key_func, timeout=30):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock_key = lock_key_func(*args, **kwargs)
            from django.core.cache import cache
            acquired = cache.add(lock_key, "locked", timeout=timeout)
            while not acquired:
                time.sleep(0.2)
                acquired = cache.add(lock_key, "locked", timeout=timeout)
            try:
                return func(*args, **kwargs)
            finally:
                cache.delete(lock_key)
        return wrapper
    return decorator

