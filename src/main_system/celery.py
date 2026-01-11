import os
import django
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main_system.settings")

# Ensure Django is fully initialized before importing models
django.setup()

from main_system.utils.tasks_base import BaseTaskWithMeta  # Import AFTER django.setup()
from main_system.utils.celery_beat_schedule import CELERY_BEAT_SCHEDULE

app = Celery("main_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Set custom base task
app.Task = BaseTaskWithMeta

# Configure Celery Beat schedule
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
app.conf.timezone = 'UTC'
