from pathlib import Path
from datetime import timedelta
import environ
import os
from rest_framework.settings import api_settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

IMIGRATION_BACKEND = "imigration-backend"

env = environ.Env(DEBUG=(bool, True))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

if os.path.exists(os.path.join(BASE_DIR, ".env")):
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
FINGERPRINT_SECRET = env("FINGERPRINT_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

# Environment
APP_ENV = env("APP_ENV", default="local")

# Force DEBUG=False in production for security
if APP_ENV == "production":
    DEBUG = False
    assert not DEBUG, "DEBUG must be False in production"

# Helper to split comma-separated env vars
def get_list_from_env(var_name, default=""):
    value = env(var_name, default=default)
    return [v.strip() for v in value.split(",") if v.strip()]



# Hosts & CORS
ALLOWED_HOSTS = get_list_from_env("ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = get_list_from_env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = get_list_from_env("CSRF_TRUSTED_ORIGINS")

CORS_ALLOW_CREDENTIALS = True

# CORS Configuration - Security: Explicit environment checks
APP_ENVIRONMENTS = ["local", "dev", "qa"]
if APP_ENV in APP_ENVIRONMENTS:
    # In non-production, allow all origins but log warning
    CORS_ALLOW_ALL_ORIGINS = True
    import logging
    logger = logging.getLogger('django')
    logger.warning("CORS_ALLOW_ALL_ORIGINS is True in non-production environment")

if APP_ENV == "production":
    CORS_ALLOW_ALL_ORIGINS = False
    # Ensure CORS_ALLOWED_ORIGINS is set in production
    if not CORS_ALLOWED_ORIGINS:
        import logging
        logger = logging.getLogger('django')
        logger.error("CORS_ALLOWED_ORIGINS is empty in production! This is a security risk.")

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
# HSTS Configuration - Production: 1 year, Dev: Disabled
if APP_ENV == "production":
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0  # Disable in dev
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

CSRF_COOKIE_DOMAIN = ".borderlink.app"


ACCESS_COOKIE_NAME = "access_token"
SESSION_COOKIE_NAME = "sessionid"
FINGERPRINT_COOKIE_NAME = "fingerprint"
MFA_VERIFIED_COOKIE_NAME = "mfa_verified"

# UK INGESTION API
UK_GOV_API_BASE_URL = env('UK_GOV_API_BASE_URL')

# AI/LLM Services
OPENAI_API_KEY = env('OPENAI_API_KEY', default=None)
AI_CALLS_LLM_MODEL = env('AI_CALLS_LLM_MODEL', default='gpt-5.2')

# Speech Services
SPEECH_TO_TEXT_PROVIDER = env('SPEECH_TO_TEXT_PROVIDER', default='google')
TEXT_TO_SPEECH_PROVIDER = env('TEXT_TO_SPEECH_PROVIDER', default='google')
GOOGLE_APPLICATION_CREDENTIALS = env('GOOGLE_APPLICATION_CREDENTIALS', default=None)
GOOGLE_SPEECH_API_KEY = env('GOOGLE_SPEECH_API_KEY', default=None)
GOOGLE_TTS_API_KEY = env('GOOGLE_TTS_API_KEY', default=None)

# AWS Services
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default=None)
AWS_REGION = env('AWS_REGION', default='us-east-1')

# S3 Storage
USE_S3_STORAGE = env.bool('USE_S3_STORAGE', default=False)
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default=None)
AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL', default=None)

# AWS Macie (Virus Scanning)
AWS_MACIE_REGION = env('AWS_MACIE_REGION', default='us-east-1')
AWS_MACIE_TEMP_BUCKET = env('AWS_MACIE_TEMP_BUCKET', default=None)

# Document Processing - OCR
OCR_BACKEND = env('OCR_BACKEND', default='tesseract')

# Document Processing - Virus Scanning
VIRUS_SCAN_BACKEND = env('VIRUS_SCAN_BACKEND', default='none')
CLAMAV_SOCKET = env('CLAMAV_SOCKET', default='/var/run/clamav/clamd.ctl')
CLAMAV_SCAN_TIMEOUT = env.int('CLAMAV_SCAN_TIMEOUT', default=30)
AWS_MACIE_SCAN_TIMEOUT = env.int('AWS_MACIE_SCAN_TIMEOUT', default=60)
MAX_VIRUS_SCAN_FILE_SIZE = env.int('MAX_VIRUS_SCAN_FILE_SIZE', default=100 * 1024 * 1024)  # 100MB
VIRUS_SCAN_FAIL_SECURE = env.bool('VIRUS_SCAN_FAIL_SECURE', default=True)

# File Storage
MEDIA_ROOT = env('MEDIA_ROOT', default=None)
MEDIA_URL = env('MEDIA_URL', default='/media/')

# Data Ingestion
DEFAULT_JURISDICTION = env('DEFAULT_JURISDICTION', default='UK')
USE_STREAMING_FOR_LARGE_DOCS = env.bool('USE_STREAMING_FOR_LARGE_DOCS', default=True)
STREAMING_THRESHOLD = env.int('STREAMING_THRESHOLD', default=10000)
REDACT_PII_BEFORE_LLM = env.bool('REDACT_PII_BEFORE_LLM', default=True)

# Payment History
PAYMENT_HISTORY_RETENTION_YEARS = env.int('PAYMENT_HISTORY_RETENTION_YEARS', default=2)

# Payment Gateways - Stripe
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default=None)
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default=None)
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default=None)

# Payment Gateways - PayPal
PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID', default=None)
PAYPAL_CLIENT_SECRET = env('PAYPAL_CLIENT_SECRET', default=None)
PAYPAL_MODE = env('PAYPAL_MODE', default='sandbox')
PAYPAL_WEBHOOK_ID = env('PAYPAL_WEBHOOK_ID', default=None)

# Payment Gateways - Adyen
ADYEN_API_KEY = env('ADYEN_API_KEY', default=None)
ADYEN_MERCHANT_ACCOUNT = env('ADYEN_MERCHANT_ACCOUNT', default=None)
ADYEN_ENVIRONMENT = env('ADYEN_ENVIRONMENT', default='test')
ADYEN_HMAC_KEY = env('ADYEN_HMAC_KEY', default=None)

# Logging Configuration
SERVICE_NAME = env('SERVICE_NAME', default='default-service')
VERSION = env('VERSION', default='1.0.0')
RELEASE = env('RELEASE', default='latest')

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
    "ai_calls",
    "ai_decisions",
    "compliance",
    "data_ingestion",
    "document_handling",
    "document_processing",
    "human_reviews",
    "immigration_cases",
    "payments",
    "rules_knowledge",
    "users_access",
]


INSTALLED_APPS += [
    # "django_celery_beat", # Removed - using Redbeat (Redis-based scheduler) instead
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
CELERY_BEAT_MAX_LOOP_INTERVAL = 60  # 1 minute

# Redbeat (Redis-based Celery Beat scheduler) Configuration
# Redbeat stores periodic task schedules in Redis instead of database
CELERY_BEAT_SCHEDULER = 'redbeat.schedulers:RedBeatScheduler'
CELERY_REDBEAT_REDIS_URL = env("CELERY_BROKER_URL")  # Use same Redis as broker
CELERY_REDBEAT_KEY_PREFIX = 'redbeat:'  # Prefix for Redis keys storing schedules
CELERY_REDBEAT_LOCK_TIMEOUT = 30  # Lock timeout in seconds

# Celery Beat Schedule (imported from celery_beat_schedule.py)
# This schedule will be loaded into Redbeat on startup
from main_system.utils.celery_beat_schedule import CELERY_BEAT_SCHEDULE
CELERY_BEAT_SCHEDULE = CELERY_BEAT_SCHEDULE


CACHE_PREFIX = "imigration_backend"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://redis:6379/0"),
        "KEY_PREFIX": CACHE_PREFIX,
        "VERSION": 1,
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
            '()': 'main_system.utils.logging_config.CustomJsonFormatter',
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
    
    # 5. Security headers middleware (add security headers)
    "main_system.middlewares.security_headers.SecurityHeadersMiddleware",

    # 5.1 Performance profiling (no-op unless PERF_PROFILE_REQUESTS=True)
    "main_system.middlewares.performance_profiler.PerformanceProfilerMiddleware",

    # 6. Django final middleware
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

# Security: Request size limits to prevent DoS attacks
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Limit number of form fields


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

    # Rate limits - Security: Adjusted for better protection
    "DEFAULT_THROTTLE_RATES": {
        "anon": "5/minute",  # Reduced from 10/min for better brute force protection
        "user": "300/minute", # Reduced from 500/min for better DoS protection
        "request_rate": "5/minute",
        "otp": "3/minute",  # Reduced from 5/min for OTP endpoints
        "refresh_token": "10/minute",
        "login": "5/minute",  # Specific rate limit for login endpoints
        "registration": "3/minute",  # Specific rate limit for registration
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


