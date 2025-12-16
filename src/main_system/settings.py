from pathlib import Path
from datetime import timedelta
import environ
import os
from rest_framework.settings import api_settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from .logging_config import CustomJsonFormatter
import logging

IMIGRATION_BACKEND = "imigration-backend"

env = environ.Env(
    DEBUG=(bool, True)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

if os.path.exists(os.path.join(BASE_DIR, ".env")):
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
FINGERPRINT_SECRET = env("FINGERPRINT_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

# Helper to split comma-separated env vars
def get_list_from_env(var_name, default=""):
    value = env(var_name, default=default)
    return [v.strip() for v in value.split(",") if v.strip()]

# Environment
APP_ENV = env("APP_ENV", default="local")

# Hosts & CORS
ALLOWED_HOSTS = get_list_from_env("ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = get_list_from_env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = get_list_from_env("CSRF_TRUSTED_ORIGINS")

CORS_ALLOW_CREDENTIALS = True

# In local dev, allow all origins if needed
APP_ENVIRONMENTS = ["local", "dev", "qa"]
if APP_ENV in APP_ENVIRONMENTS:
    CORS_ALLOW_ALL_ORIGINS = True

if APP_ENV == "production":
    CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_HEADERS = [
    'content-type',
    'x-csrftoken',
    'authorization',
    'accept',
    'origin',
    'user-agent',
    'referer',
]


SITE_NAME = env("SITE_NAME")
SITE_ID = 1

APPEND_SLASH = True


SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_COOKIE_HTTPONLY=False
SESSION_COOKIE_HTTPONLY=True
X_FRAME_OPTIONS = "DENY"

CSRF_COOKIE_DOMAIN = ".borderlink.app"


ACCESS_COOKIE_NAME = "access_token"
SESSION_COOKIE_NAME = "sessionid"
FINGERPRINT_COOKIE_NAME = "fingerprint"
MFA_VERIFIED_COOKIE_NAME = "mfa_verified"

SANDBOX_PUBLIC_KEY=env("SANDBOX_PUBLIC_KEY")
SANDBOX_SECRET_KEY=env("SANDBOX_SECRET_KEY")
PRODUCT_MONO_ID=env("PRODUCT_MONO_ID")
MONO_BASE_URL=env("MONO_BASE_URL")
MONO_WEBHOOK_SECRET_KEY =env("MONO_WEBHOOK_SECRET_KEY")

#FOREX EXCHANGE RATE
OPEN_EXCHANGE_RATE_API_KEY=env('OPEN_EXCHANGE_RATE_API_KEY')
OPEN_EXCHANGE_RATE_BASE_URL=env('OPEN_EXCHANGE_RATE_BASE_URL')


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django.contrib.sites", #required for email verification links
    "guardian", # required for Guardian
    # Django-knox
    "knox",
    "corsheaders", # for CORS support

    #my apps
    "ai_decisions",
    "compliance",
    "data_ingestion",
    "document_handling",
    "human_reviews",
    "immigration_cases",
    "payments",
    "rules_knowledge",
    "users_access",
]


INSTALLED_APPS += [
    "django_celery_beat", # for periodic tasks
    "django_celery_results",
    "django_extensions", # for development utilities
    "django_prometheus", # for monitoring
]


if APP_ENV in ["production", "staging"]:
    SENTRY_DSN = env("SENTRY_DSN")

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            LoggingIntegration(
                level=logging.INFO, # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
        ],
        environment=APP_ENV,
        traces_sample_rate=0.5,  # Adjust for performance monitoring
        send_default_pii=True,
        enable_tracing=True,
        before_send=lambda event, hint: event,
        ignore_errors=[],
        debug=False,
        max_breadcrumbs=200,
        server_name=IMIGRATION_BACKEND,
    )



# CELERY SETTINGS
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = env("CELERY_TASK_SERIALIZER")
CELERY_RESULT_SERIALIZER = env("CELERY_RESULT_SERIALIZER")
CELERY_TIMEZONE = env("CELERY_TIMEZONE")
CELERY_CACHE_BACKEND = 'django-cache'
DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH = 255
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes



CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://redis:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# Token settings
ACCESS_TOKEN_TTL = timedelta(minutes=15)
ACCESS_TOKEN_REFRESH_GRACE_PERIOD = timedelta(minutes=2)
ACCESS_COOKIE_NAME = "access_token"


# LOGGING SETTINGS
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'main_system.logging_config.CustomJsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(pathname)s:%(lineno)d %(funcName)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout',
        },
        'json_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'logs/app.json',
            'backupCount': 7,
            'formatter': 'json',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'logs/celery.json',
            'backupCount': 7,
            'formatter': 'json',
        },
        'db': {
            'level': 'INFO',
            'class': 'compliance.handlers.logging_handler.LazyDatabaseLogHandler',
            'formatter': 'json'
        }
    },
    'root': {
        'handlers': ['console', 'json_file'],
        'level': 'INFO',
        'propagate': True,
    },
    'loggers': {
        'celery': {
            'handlers': ['console', 'celery_file', 'json_file', 'db'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'json_file', 'db'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console', 'json_file'],  # Exclude DB logging from DB handler (avoids loops)
            'level': 'ERROR',
            'propagate': False,
        }
    },
}



AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend", #Default Django backend,
    "guardian.backends.ObjectPermissionBackend", # Guardian backend
)

AUTH_MAIN_BACKEND = "django.contrib.auth.backends.ModelBackend"

MIDDLEWARE = [
    # Django Prometheus before middleware
    "django_prometheus.middleware.PrometheusBeforeMiddleware",

    # 1. CORS should be first
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",

    # 2. Security and common Django middlewares
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    # 3. CSRF and authentication
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    'main_system.middlewares.prevent_back_button.PreventBackButtonMiddleware',

    # 4. Custom middleware
    "main_system.middlewares.slash_fix.EnforceTrailingSlashMiddleware",
    "main_system.middlewares.device_access_manager.DeviceSessionRefreshMiddleware",
    "main_system.middlewares.two_factor_auth.TwoFactorAuthMiddleware",

    # 5. Django final middleware
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Django Prometheus after middleware
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]



ROOT_URLCONF = "main_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "main_system.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_DATABASE"),
        "USER": env("DB_USERNAME"),
        "PASSWORD": env("DB_PASSWORD"),
        "PORT": env("DB_PORT"),
        "HOST": env("DB_HOST"),
        "CONN_MAX_AGE": int(env("CONN_MAX_AGE")),
        "CONN_HEALTH_CHECK": True,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# REST FRAMEWORK SETTINGS
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("main_system.middlewares.cookie_access_only.CookieAccessOnlyTokenAuthentication",),
    # "DEFAULT_AUTHENTICATION_CLASSES": ("knox.auth.TokenAuthentication",),
    "NON_FIELD_ERRORS_KEY": "error",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend",],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",  # For all unauthenticated requests
        "rest_framework.throttling.UserRateThrottle",  # For all authenticated requests
        "rest_framework.throttling.ScopedRateThrottle", # For custom scoped throttles
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],

    # Rate limits
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10/minute",  # All endpoints accessed without token
        "user": "500/minute", # All endpoints accessed with token
        "request_rate": "5/minute",
        "otp": "5/minute",
        "refresh_token": "10/minute",
    },

    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


KNOX_TOKEN_MODEL = "knox.AuthToken"


AUTH_USER_MODEL = "users_access.User"

USE_X_FORWARDED_HOST = True

REST_KNOX = {
    'SECURE_HASH_ALGORITHM': 'hashlib.sha512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 255,
    'TOKEN_TTL': timedelta(minutes=24*60), # 1 day
    'USER_SERIALIZER': 'knox.serializers.UserSerializer',
    'TOKEN_LIMIT_PER_USER': 5, # prevent token sprawl
    'AUTO_REFRESH': False,
    'AUTO_REFRESH_MAX_TTL': None,
    'MIN_REFRESH_INTERVAL': 60,
    'AUTH_HEADER_PREFIX': 'Token',
    'EXPIRY_DATETIME_FORMAT': api_settings.DATETIME_FORMAT,
    'TOKEN_MODEL': 'knox.AuthToken',
}


# Email settings
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
if APP_ENV in ['dev', 'local']:
    EMAIL_BACKEND = env("EMAIL_BACKEND")
    MAILER_EMAIL_BACKEND = env("EMAIL_BACKEND")
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default=None) or None
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default=None) or None
    EMAIL_PORT = env.int("EMAIL_PORT")
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
else:
    EMAIL_BACKEND = env("EMAIL_BACKEND")
    MAILER_EMAIL_BACKEND = env("EMAIL_BACKEND")
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = env("EMAIL_PORT")
    EMAIL_USE_TLS = True


ENFORCE_2FA_PATHS = [
]

import logging.config
logging.config.dictConfig(LOGGING)