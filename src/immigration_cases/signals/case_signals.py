from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from immigration_cases.models.case import Case
from users_access.services.notification_service import NotificationService
from users_access.tasks.email_tasks import send_case_status_update_email_task


@receiver(post_save, sender=Case)
def handle_case_status_change(sender, instance, created, **kwargs):
    """
    Signal handler for case status changes.
    Sends notifications and emails when case status changes.
    """
    if created:
        # New case created
        NotificationService.create_notification(
            user_id=str(instance.user.id),
            notification_type='case_status_update',
            title='Case Created',
            message=f'Your immigration case has been created successfully.',
            priority='medium',
            related_entity_type='case',
            related_entity_id=str(instance.id),
            metadata={'status': instance.status}
        )
    else:
        # Check if status changed
        if hasattr(instance, '_previous_status'):
            previous_status = instance._previous_status
            if previous_status != instance.status:
                # Status changed - send notification and email
                status_messages = {
                    'draft': 'Your case is in draft status.',
                    'evaluated': 'Your case has been evaluated. Check your eligibility results.',
                    'awaiting_review': 'Your case is awaiting human review.',
                    'reviewed': 'Your case has been reviewed by our team.',
                    'closed': 'Your case has been closed.',
                }
                
                message = status_messages.get(instance.status, f'Your case status has been updated to {instance.status}.')
                
                # Create in-app notification
                NotificationService.create_notification(
                    user_id=str(instance.user.id),
                    notification_type='case_status_update',
                    title=f'Case Status Updated: {instance.status.title()}',
                    message=message,
                    priority='high' if instance.status in ['awaiting_review', 'reviewed'] else 'medium',
                    related_entity_type='case',
                    related_entity_id=str(instance.id),
                    metadata={'status': instance.status, 'previous_status': previous_status}
                )
                
                # Send email notification (async via Celery)
                send_case_status_update_email_task.delay(
                    user_id=str(instance.user.id),
                    case_id=str(instance.id),
                    status=instance.status,
                    previous_status=previous_status
                )


@receiver(pre_save, sender=Case)
def store_previous_status(sender, instance, **kwargs):
    """
    Store previous status before save to detect changes.
    """
    if instance.pk:
        try:
            previous_instance = Case.objects.get(pk=instance.pk)
            instance._previous_status = previous_instance.status
        except Case.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

