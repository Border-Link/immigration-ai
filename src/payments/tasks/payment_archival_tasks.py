"""
Payment History Archival Tasks

Periodic tasks to archive old payment history entries.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from payments.models.payment_history import PaymentHistory
from django.conf import settings

logger = logging.getLogger('django')

# Retention period: archive history older than 2 years
HISTORY_RETENTION_YEARS = getattr(settings, 'PAYMENT_HISTORY_RETENTION_YEARS', 2)


@shared_task(bind=True, max_retries=3)
def archive_old_payment_history(self):
    """
    Archive payment history entries older than retention period.
    
    This task moves old history entries to an archive table or marks them for deletion.
    For now, it deletes old entries. In production, you might want to move them to an archive table.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=HISTORY_RETENTION_YEARS * 365)
        
        # Get old history entries
        old_history = PaymentHistory.objects.filter(created_at__lt=cutoff_date)
        count = old_history.count()
        
        if count > 0:
            # For now, we'll just delete old entries
            # In production, you might want to move them to an archive table
            old_history.delete()
            logger.info(f"Archived {count} payment history entries older than {HISTORY_RETENTION_YEARS} years")
        else:
            logger.info("No payment history entries to archive")
        
        return {'archived_count': count}
        
    except Exception as e:
        logger.error(f"Error archiving payment history: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300, max_retries=3)
