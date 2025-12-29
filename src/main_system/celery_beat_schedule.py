"""
Celery Beat schedule configuration for periodic tasks.
This file defines all scheduled tasks that run automatically.
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Daily ingestion of all active data sources
    'ingest-all-active-sources-daily': {
        'task': 'data_ingestion.tasks.ingestion_tasks.ingest_all_active_sources_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM UTC
        'options': {'expires': 3600}  # Task expires after 1 hour
    },
    
    # Hourly ingestion check for high-frequency sources
    'ingest-high-frequency-sources': {
        'task': 'data_ingestion.tasks.ingestion_tasks.ingest_all_active_sources_task',
        'schedule': crontab(minute=0),  # Run every hour
        'options': {'expires': 1800}  # Task expires after 30 minutes
    },
    
    # Weekly cleanup of old audit logs (archive logs older than 1 year)
    'archive-old-audit-logs': {
        'task': 'compliance.tasks.audit_log_tasks.archive_old_audit_logs_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Run weekly on Sunday at 3 AM
        'options': {'expires': 7200}  # Task expires after 2 hours
    },
    
    # Daily check for SLA deadlines (review assignments approaching deadline)
    'check-review-sla-deadlines': {
        'task': 'human_reviews.tasks.review_tasks.check_review_sla_deadlines_task',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM UTC
        'options': {'expires': 1800}
    },
    
    # Daily notification for pending rule validation tasks
    'notify-pending-rule-validation-tasks': {
        'task': 'data_ingestion.tasks.rule_validation_tasks.notify_pending_rule_validation_tasks_task',
        'schedule': crontab(hour=10, minute=0),  # Run daily at 10 AM UTC
        'options': {'expires': 1800}
    },
}

