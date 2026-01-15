from functools import wraps
import time

from main_system.utils.cache_utils import cache_add, cache_delete

def with_lock(lock_key_func, timeout=30):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock_key = lock_key_func(*args, **kwargs)
            acquired = cache_add(lock_key, "locked", timeout=timeout)
            while not acquired:
                time.sleep(0.2)
                acquired = cache_add(lock_key, "locked", timeout=timeout)
            try:
                return func(*args, **kwargs)
            finally:
                cache_delete(lock_key)
        return wrapper
    return decorator

