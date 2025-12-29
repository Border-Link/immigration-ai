from celery import shared_task
import logging
from main_system.tasks_base import BaseTaskWithMeta
from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector
from users_access.services.notification_service import NotificationService
from users_access.tasks.email_tasks import send_rule_validation_task_email_task

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def notify_pending_rule_validation_tasks_task(self):
    """
    Celery task to notify reviewers/admins about pending rule validation tasks.
    This task runs daily via Celery Beat.
    
    Returns:
        Dict with notification results
    """
    try:
        logger.info("Starting pending rule validation task notification")
        
        # Get all pending/open validation tasks
        pending_tasks = RuleValidationTaskSelector.get_by_status('pending')
        
        notified_count = 0
        
        for task in pending_tasks:
            if task.assigned_to:
                # Task is assigned - notify assigned reviewer
                NotificationService.create_notification(
                    user_id=str(task.assigned_to.id),
                    notification_type='rule_validation_task',
                    title='Pending Rule Validation Task',
                    message=f'You have a pending rule validation task that requires attention.',
                    priority='medium',
                    related_entity_type='rule_validation_task',
                    related_entity_id=str(task.id),
                    metadata={'status': task.status}
                )
                
                send_rule_validation_task_email_task.delay(
                    reviewer_id=str(task.assigned_to.id),
                    task_id=str(task.id)
                )
                notified_count += 1
            else:
                # Task not assigned - notify all admins/reviewers
                from users_access.selectors.user_selector import UserSelector
                admins = UserSelector.get_by_role('admin')
                reviewers = UserSelector.get_by_role('reviewer')
                
                for admin in admins:
                    NotificationService.create_notification(
                        user_id=str(admin.id),
                        notification_type='rule_validation_task',
                        title='Unassigned Rule Validation Task',
                        message=f'A rule validation task requires assignment.',
                        priority='medium',
                        related_entity_type='rule_validation_task',
                        related_entity_id=str(task.id)
                    )
        
        logger.info(f"Notified {notified_count} reviewers about pending validation tasks")
        
        return {
            'success': True,
            'notified_count': notified_count,
            'total_pending': pending_tasks.count()
        }
        
    except Exception as e:
        logger.error(f"Error notifying about pending rule validation tasks: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)

