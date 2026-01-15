"""
Test settings for pytest/django.

Goals:
- Remove hard dependency on external services (Redis/Sentry/etc.) for unit/integration tests.
- Keep production settings unchanged.
"""

from .settings import *  # noqa: F403,F401


# -------------------------
# Core test toggles
# -------------------------

# Make sure Django treats this as a non-production environment.
APP_ENV = "test"
DEBUG = False


# -------------------------
# Caching: avoid Redis in tests
# -------------------------
# Many services are wrapped with @cache_result; using Redis in tests frequently causes
# failures (NOAUTH, connection refused, etc.) and also adds flakiness.
CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "pytest",
    }
}


# -------------------------
# Speed / determinism
# -------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


# -------------------------
# Database: avoid external Postgres in tests
# -------------------------
# The production settings expect a Postgres host (often a docker service name like "postgres").
# For unit/integration tests, default to SQLite to keep the suite runnable without external
# infrastructure. This does not affect production settings.
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# -------------------------
# Celery: run tasks inline during tests (if used)
# -------------------------

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


# -------------------------
# Observability: disable Sentry in tests
# -------------------------

SENTRY_DSN = None


