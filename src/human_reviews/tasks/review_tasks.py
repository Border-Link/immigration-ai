from celery import shared_task
import logging
from django.utils import timezone
from datetime import timedelta
from main_system.utils.tasks_base import BaseTaskWithMeta
from human_reviews.selectors.review_selector import ReviewSelector
from users_access.services.notification_service import NotificationService

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def check_review_sla_deadlines_task(self):
    """
    Celery task to check for reviews approaching SLA deadlines.
    Sends notifications to reviewers and escalates if needed.
    This task runs daily via Celery Beat.
    
    Returns:
        Dict with SLA check results
    """
    try:
        logger.info("Starting review SLA deadline check")
        
        # Get all in-progress reviews
        in_progress_reviews = ReviewSelector.get_by_status('in_progress')
        
        # Default SLA: 7 days, urgent: 2 days
        urgent_deadline = timezone.now() + timedelta(days=2)
        normal_deadline = timezone.now() + timedelta(days=7)
        
        urgent_count = 0
        approaching_count = 0
        
        for review in in_progress_reviews:
            if review.due_date:
                days_remaining = (review.due_date - timezone.now()).days
                
                if days_remaining <= 2:
                    # Urgent - approaching deadline
                    urgent_count += 1
                    if review.reviewer:
                        NotificationService.create_notification(
                            user_id=str(review.reviewer.id),
                            notification_type='sla_deadline',
                            title='Urgent: Review Deadline Approaching',
                            message=f'Your review for case {review.case.id} is due in {days_remaining} days.',
                            priority='urgent',
                            related_entity_type='review',
                            related_entity_id=str(review.id),
                            metadata={'days_remaining': days_remaining}
                        )
                elif days_remaining <= 3:
                    # Approaching deadline
                    approaching_count += 1
                    if review.reviewer:
                        NotificationService.create_notification(
                            user_id=str(review.reviewer.id),
                            notification_type='sla_deadline',
                            title='Review Deadline Approaching',
                            message=f'Your review for case {review.case.id} is due in {days_remaining} days.',
                            priority='high',
                            related_entity_type='review',
                            related_entity_id=str(review.id),
                            metadata={'days_remaining': days_remaining}
                        )
        
        logger.info(f"SLA check completed: {urgent_count} urgent, {approaching_count} approaching")
        
        return {
            'success': True,
            'urgent_reviews': urgent_count,
            'approaching_reviews': approaching_count,
            'total_checked': in_progress_reviews.count()
        }
        
    except Exception as e:
        logger.error(f"Error checking review SLA deadlines: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)

