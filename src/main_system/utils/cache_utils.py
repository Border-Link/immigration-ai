"""
Application caching utilities.

Goals:
- **Prevent cross-user data leakage** by defaulting to per-user scoping when a user
  (or request.user) is available.
- **Make invalidation reliable** without requiring wildcard deletion. We use a
  namespace-version scheme: cached keys embed the current namespace version; writes
  simply bump the namespace version to invalidate all related reads.
- Work across cache backends used in this repo:
  - Production: `django-redis`
  - Tests: `LocMemCache`

Important design notes:
- This module intentionally centralizes all application caching behavior.
- Prefer caching **stable, serializable data**. Caching ORM objects/querysets works
  with pickle-capable backends but can have surprising behavior; use judiciously.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from django.core.cache import cache
from django.conf import settings

_SENTINEL = object()
_logger = None

# Internal prefixes for utility keys. (These are still subject to Django's KEY_PREFIX.)
_NSVER_PREFIX = "__bl_nsver__:"


def _safe_json(value: Any) -> str:
    """
    Create a stable string representation for cache key material.
    """
    if value is None:
        return "null"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    except Exception:
        # Last resort: repr() is stable enough for keying within a process/version.
        return repr(value)


def _extract_user_from_bound_args(bound_args: inspect.BoundArguments) -> Optional[Any]:
    """
    Best-effort extraction of a Django user from common argument patterns.
    """
    args = bound_args.arguments
    if "user" in args:
        return args.get("user")
    req = args.get("request")
    if req is not None:
        return getattr(req, "user", None)
    return None


# -------------------------
# Namespace versioning
# -------------------------

def _namespace_version_key(namespace: str) -> str:
    return f"{_NSVER_PREFIX}{namespace}"


def get_namespace_version(namespace: str) -> int:
    """
    Always returns a namespace version. Creates it if missing.
    """
    if not namespace:
        return 1
    # Namespace versions should not expire; they are invalidation counters.
    return int(cache.get_or_set(_namespace_version_key(namespace), 1, timeout=None))


def bump_namespace(namespace: str) -> None:
    """
    Bump a namespace version.

    This is safe in multi-worker environments (Redis) and works for LocMemCache.
    """
    if not namespace:
        return
    key = _namespace_version_key(namespace)
    # Ensure it exists, then increment.
    cache.add(key, 1, timeout=None)
    try:
        cache.incr(key)
    except Exception:
        # Some backends may raise if key doesn't exist or isn't an int.
        # Fall back to a simple set based on the current value.
        cache.set(key, get_namespace_version(namespace) + 1, timeout=None)


# -------------------------
# Key builder
# -------------------------

def make_cache_key(
    *,
    namespace: Optional[str],
    namespace_version: int,
    func_qualname: str,
    user_scope: str,
    user_id: str,
    key_material: Dict[str, Any],
) -> str:
    """
    Build a compact cache key.
    We hash the payload to avoid exceeding backend key length limits.
    """
    payload = {
        "ns": namespace or "",
        "nsv": int(namespace_version),
        "fn": func_qualname,
        "scope": user_scope,
        "uid": user_id,
        "k": {k: _safe_json(v) for k, v in key_material.items()},
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"blcache:{digest}"


# -------------------------
# Public API
# -------------------------

def cache_get(key: str, default: Any = None) -> Any:
    return cache.get(key, default)


def cache_set(key: str, value: Any, timeout: Optional[int] = None) -> None:
    cache.set(key, value, timeout=timeout)


def cache_add(key: str, value: Any, timeout: Optional[int] = None) -> bool:
    return bool(cache.add(key, value, timeout=timeout))


def cache_incr(key: str, delta: int = 1) -> int:
    return int(cache.incr(key, delta=delta))


def cache_delete(key: str) -> None:
    cache.delete(key)

def cache_clear() -> None:
    cache.clear()


def cache_get_or_set(key: str, default_factory: Callable[[], Any], timeout: Optional[int] = None) -> Any:
    """
    Like Django's get_or_set, but supports callables consistently across backends.
    """
    value = cache.get(key, _SENTINEL)
    if value is not _SENTINEL:
        return value
    value = default_factory()
    cache.set(key, value, timeout=timeout)
    return value


def cache_result(
    timeout: int = 3600,
    keys: Optional[Iterable[str]] = None,
    namespace: Optional[Callable[..., str]] = None,
    *,
    user_scope: str = "auto",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Cache decorator.

    Args:
        timeout: Cache TTL in seconds.
        keys: Names of bound arguments to include in the cache key.
        namespace: Callable returning a namespace string. The namespace version is embedded
                  in the cache key; bumping the namespace invalidates all related reads.
        user_scope:
            - "auto": If a user (or request.user) is present, scope per-user; otherwise global.
            - "user": Require an authenticated user; if missing, skip caching.
            - "global": Never vary by user.
    """
    keys = list(keys or [])

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)
        func_qualname = f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            global _logger
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            ns = namespace(*args, **kwargs) if namespace else None
            nsv = get_namespace_version(ns) if ns else 1

            user = _extract_user_from_bound_args(bound)
            is_authenticated = bool(getattr(user, "is_authenticated", False))
            resolved_user_id = str(getattr(user, "id", "anonymous"))

            resolved_scope = user_scope
            if user_scope == "auto":
                resolved_scope = "user" if user is not None else "global"

            if resolved_scope == "user":
                if not is_authenticated:
                    # Don't cache user-scoped reads without a concrete authenticated user.
                    return func(*args, **kwargs)
            elif resolved_scope == "global":
                resolved_user_id = "global"
            else:
                # Unknown scope value: fail safe by skipping caching.
                return func(*args, **kwargs)

            key_material: Dict[str, Any] = {}
            self_obj = arguments.get("self")
            if self_obj is not None:
                key_material["class"] = self_obj.__class__.__name__
            for k in keys:
                key_material[k] = arguments.get(k)

            cache_key = make_cache_key(
                namespace=ns,
                namespace_version=nsv,
                func_qualname=func_qualname,
                user_scope=resolved_scope,
                user_id=resolved_user_id,
                key_material=key_material,
            )

            cache_data = cache.get(cache_key, _SENTINEL)
            if cache_data is not _SENTINEL:
                if getattr(settings, "PERF_PROFILE_CACHE", False):
                    if _logger is None:
                        import logging
                        _logger = logging.getLogger("django")
                    _logger.info(
                        "PERF cache=hit ns=%s scope=%s fn=%s",
                        ns or "",
                        resolved_scope,
                        func_qualname,
                    )
                return cache_data

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            if getattr(settings, "PERF_PROFILE_CACHE", False):
                if _logger is None:
                    import logging
                    _logger = logging.getLogger("django")
                _logger.info(
                    "PERF cache=miss ns=%s scope=%s fn=%s",
                    ns or "",
                    resolved_scope,
                    func_qualname,
                )
            return result

        return wrapper

    return decorator


def invalidate_cache(
    namespace_adapter: Callable[..., str],
    *,
    predicate: Optional[Callable[[Any], bool]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to invalidate (bump) a namespace after a successful write.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            should_invalidate = True if predicate is None else bool(predicate(result))
            if should_invalidate:
                ns = namespace_adapter(*args, **kwargs)
                bump_namespace(ns)
            return result

        return wrapper

    return decorator