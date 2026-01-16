"""
Test settings for pytest/django.

Goals:
- Remove hard dependency on external services (Redis/Sentry/etc.) for unit/integration tests.
- Keep production settings unchanged.

Important:
- main_system.settings reads several required environment variables at import time.
  For tests, we provide safe defaults here so the suite can run in clean environments
  (CI, sandboxes) without a .env file.
"""

from __future__ import annotations

import os

# -------------------------
# Minimal required env vars (import-time)
# -------------------------
# SECURITY: These are non-production defaults used only for tests.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "test-field-encryption-key")
os.environ.setdefault("FINGERPRINT_SECRET", "test-fingerprint-secret")
os.environ.setdefault("SITE_NAME", "Borderlink Test")
os.environ.setdefault("UK_GOV_API_BASE_URL", "https://example.test")

# Celery/Redis (overridden below, but required for settings import)
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_TASK_SERIALIZER", "json")
os.environ.setdefault("CELERY_RESULT_SERIALIZER", "json")
os.environ.setdefault("CELERY_TIMEZONE", "UTC")

# Database (overridden below, but required for settings import)
os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")
os.environ.setdefault("DB_DATABASE", ":memory:")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("CONN_MAX_AGE", "0")

# Email (overridden below, but required for settings import)
os.environ.setdefault("DEFAULT_FROM_EMAIL", "no-reply@test.local")
os.environ.setdefault("EMAIL_BACKEND", "django.core.mail.backends.locmem.EmailBackend")
os.environ.setdefault("EMAIL_HOST", "localhost")
os.environ.setdefault("EMAIL_HOST_USER", "")
os.environ.setdefault("EMAIL_HOST_PASSWORD", "")
os.environ.setdefault("EMAIL_PORT", "1025")

# Observability
os.environ.setdefault("SENTRY_DSN", "")

from .settings import *  # noqa: F403,F401,E402

import copy


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


# -------------------------
# Logging: avoid filesystem / DB handlers in tests
# -------------------------
# Some sandbox/CI environments do not expose files under `logs/` (or they may be ignored),
# and DB-backed log handlers can introduce side-effects during app init.
#
# In production we write structured logs to files + DB. In tests we keep only console logging.
LOGGING = copy.deepcopy(LOGGING)  # noqa: F405

# Replace file/db handlers with NullHandler (safe even if referenced elsewhere)
for _handler_name in ("json_file", "celery_file", "db"):
    if _handler_name in LOGGING.get("handlers", {}):
        LOGGING["handlers"][_handler_name] = {"class": "logging.NullHandler"}

# Root logger: console only
if "root" in LOGGING and "handlers" in LOGGING["root"]:
    LOGGING["root"]["handlers"] = ["console"]

# Named loggers: strip file/db handlers
for _logger_name in ("celery", "django", "django.db.backends"):
    if _logger_name in LOGGING.get("loggers", {}):
        LOGGING["loggers"][_logger_name]["handlers"] = [
            h for h in LOGGING["loggers"][_logger_name].get("handlers", []) if h == "console"
        ]

