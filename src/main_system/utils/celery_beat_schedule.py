"""
Celery Beat schedule configuration for periodic tasks.
This file defines all scheduled tasks that run automatically.
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Weekly ingestion of UK data sources (optimized for weekly schedule)
    'ingest-uk-sources-weekly': {
        'task': 'data_ingestion.tasks.ingestion_tasks.ingest_uk_sources_weekly_task',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Run weekly on Sunday at 2 AM UTC
        'options': {'expires': 7200}  # Task expires after 2 hours
    },
    
    # Daily ingestion of all active data sources (for other jurisdictions)
    'ingest-all-active-sources-daily': {
        'task': 'data_ingestion.tasks.ingestion_tasks.ingest_all_active_sources_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM UTC
        'options': {'expires': 3600}  # Task expires after 1 hour
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
    
    # Poll pending/processing payments every 15 minutes
    'poll-pending-payments': {
        'task': 'payments.tasks.payment_tasks.poll_pending_payments_task',
        'schedule': crontab(minute='*/15'),  # Run every 15 minutes
        'options': {'expires': 900}  # Task expires after 15 minutes
    },
    
    # Retry failed payments every hour
    'retry-failed-payments': {
        'task': 'payments.tasks.payment_tasks.retry_failed_payments_task',
        'schedule': crontab(minute=0),  # Run every hour
        'options': {'expires': 3600}  # Task expires after 1 hour
    },
}

