from celery import shared_task
import logging
from django.utils import timezone
from datetime import timedelta
from main_system.utils.tasks_base import BaseTaskWithMeta
from compliance.selectors.audit_log_selector import AuditLogSelector

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def archive_old_audit_logs_task(self):
    """
    Celery task to archive audit logs older than 1 year.
    This task runs weekly via Celery Beat.
    
    Returns:
        Dict with archiving results
    """
    try:
        logger.info("Starting audit log archiving task")
        
        # Get logs older than 1 year
        one_year_ago = timezone.now() - timedelta(days=365)
        old_logs = AuditLogSelector.get_by_date_range(end_date=one_year_ago)
        
        count = old_logs.count()
        
        # Archive to cold storage (S3 or similar)
        # For now, we'll just log the count
        # In production, implement actual archiving logic
        
        logger.info(f"Found {count} audit logs to archive (older than 1 year)")
        
        # Mark as archived (if you add an archived field) or move to archive table
        # For now, we'll just return the count
        
        return {
            'success': True,
            'logs_to_archive': count,
            'message': f'Found {count} logs to archive'
        }
        
    except Exception as e:
        logger.error(f"Error archiving audit logs: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)

