import os
import sys
import django
import logging
from celery import Celery

# Configure logging early to ensure errors are captured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main_system.settings")

# Initialize Django
try:
    django.setup()
except Exception as e:
    logger.error(f"Failed to setup Django: {e}", exc_info=True)
    sys.exit(1)

# Import celery configuration
try:
    from main_system.utils.tasks_base import BaseTaskWithMeta  # Import AFTER django.setup()
    from main_system.utils.celery_beat_schedule import CELERY_BEAT_SCHEDULE
except ImportError as e:
    logger.error(f"Failed to import celery configuration: {e}", exc_info=True)
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error importing celery configuration: {e}", exc_info=True)
    sys.exit(1)

# Create Celery app
app = Celery("main_system")

# Load configuration from Django settings
try:
    app.config_from_object("django.conf:settings", namespace="CELERY")
    logger.info("Celery configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load celery configuration: {e}", exc_info=True)
    sys.exit(1)

# Autodiscover tasks
try:
    app.autodiscover_tasks()
except Exception as e:
    logger.error(f"Failed to autodiscover tasks: {e}", exc_info=True)
    # Don't exit here - allow celery to start even if some tasks fail to load
    # This prevents the entire service from crashing due to one bad task

# Set custom base task
app.Task = BaseTaskWithMeta

# Configure Celery Beat schedule for Redbeat (Redis-based scheduler)
try:
    app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
    app.conf.timezone = 'UTC'
    
    # Redbeat configuration - stores schedule in Redis
    # Redbeat uses Redis keys to store periodic tasks, no database required
    app.conf.redbeat_redis_url = app.conf.broker_url  # Use same Redis as broker
    app.conf.redbeat_key_prefix = 'redbeat:'  # Prefix for Redis keys
except Exception as e:
    logger.error(f"Failed to configure celery beat schedule: {e}", exc_info=True)
    sys.exit(1)

# Verify Redis connection for Redbeat
try:
    import redis
    from urllib.parse import urlparse
    
    # Parse broker URL to get Redis connection details
    broker_url = app.conf.broker_url
    parsed = urlparse(broker_url)
    
    # Connect to Redis to verify it's accessible
    redis_client = redis.Redis(
        host=parsed.hostname or 'localhost',
        port=parsed.port or 6379,
        db=int(parsed.path.lstrip('/')) if parsed.path else 0,
        password=parsed.password,
        socket_connect_timeout=5
    )
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis connection check failed - Redbeat requires Redis access: {e}")
    logger.warning("Celery beat will attempt to connect at startup")
    # Don't exit - let celery beat try to connect
