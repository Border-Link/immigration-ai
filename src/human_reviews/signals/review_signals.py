from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from human_reviews.models.review import Review
from users_access.services.notification_service import NotificationService
from users_access.tasks.email_tasks import send_review_assignment_email_task, send_review_completed_email_task
import logging

logger = logging.getLogger('django')


@receiver(pre_save, sender=Review)
def store_previous_review_state(sender, instance, **kwargs):
    """
    Store previous reviewer and status before save to detect changes.
    """
    if instance.pk:
        try:
            previous_instance = Review.objects.get(pk=instance.pk)
            instance._previous_status = previous_instance.status
            instance._previous_reviewer = previous_instance.reviewer
        except Review.DoesNotExist:
            instance._previous_status = None
            instance._previous_reviewer = None
    else:
        instance._previous_status = None
        instance._previous_reviewer = None


@receiver(post_save, sender=Review)
def handle_review_changes(sender, instance, created, **kwargs):
    """
    Signal handler for review changes.
    - Sends notification when review is assigned
    - Sends notification when review is completed
    - Sends email notifications
    """
    if created:
        # New review created
        if instance.reviewer:
            # Review was assigned immediately
            NotificationService.create_notification(
                user_id=str(instance.reviewer.id),
                notification_type='review_assigned',
                title='New Review Assigned',
                message=f'You have been assigned a new review for case {instance.case.id}.',
                priority='high',
                related_entity_type='review',
                related_entity_id=str(instance.id),
                metadata={
                    'case_id': str(instance.case.id),
                    'status': instance.status
                }
            )
            
            # Send email to reviewer
            send_review_assignment_email_task.delay(
                reviewer_id=str(instance.reviewer.id),
                review_id=str(instance.id),
                case_id=str(instance.case.id)
            )
    else:
        # Review updated - check for status changes
        if hasattr(instance, '_previous_status'):
            previous_status = instance._previous_status
            
            # Reviewer assigned
            if hasattr(instance, '_previous_reviewer'):
                previous_reviewer = instance._previous_reviewer
                if previous_reviewer != instance.reviewer and instance.reviewer:
                    NotificationService.create_notification(
                        user_id=str(instance.reviewer.id),
                        notification_type='review_assigned',
                        title='Review Assigned to You',
                        message=f'You have been assigned a review for case {instance.case.id}.',
                        priority='high',
                        related_entity_type='review',
                        related_entity_id=str(instance.id),
                        metadata={
                            'case_id': str(instance.case.id),
                            'status': instance.status
                        }
                    )
                    
                    send_review_assignment_email_task.delay(
                        reviewer_id=str(instance.reviewer.id),
                        review_id=str(instance.id),
                        case_id=str(instance.case.id)
                    )
            
            # Review completed
            if previous_status != 'completed' and instance.status == 'completed':
                # Notify reviewer
                if instance.reviewer:
                    NotificationService.create_notification(
                        user_id=str(instance.reviewer.id),
                        notification_type='review_completed',
                        title='Review Completed',
                        message=f'Your review for case {instance.case.id} has been marked as completed.',
                        priority='medium',
                        related_entity_type='review',
                        related_entity_id=str(instance.id)
                    )
                
                # Notify case owner
                NotificationService.create_notification(
                    user_id=str(instance.case.user.id),
                    notification_type='review_completed',
                    title='Case Review Completed',
                    message=f'Your case has been reviewed. Check the results.',
                    priority='high',
                    related_entity_type='case',
                    related_entity_id=str(instance.case.id),
                    metadata={'review_id': str(instance.id)}
                )
                
                # Send email to case owner
                send_review_completed_email_task.delay(
                    user_id=str(instance.case.user.id),
                    review_id=str(instance.id),
                    case_id=str(instance.case.id)
                )

