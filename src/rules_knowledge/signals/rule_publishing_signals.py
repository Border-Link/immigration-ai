from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from users_access.services.notification_service import NotificationService
from users_access.tasks.email_tasks import send_rule_change_notification_email_task
from immigration_cases.selectors.case_selector import CaseSelector
import logging

logger = logging.getLogger('django')

# Track previous state to detect when is_published changes
_previous_is_published = {}


@receiver(pre_save, sender=VisaRuleVersion)
def track_rule_version_state(sender, instance, **kwargs):
    """Track previous state of is_published before save."""
    if instance.pk:
        try:
            old_instance = VisaRuleVersion.objects.get(pk=instance.pk)
            _previous_is_published[instance.pk] = old_instance.is_published
        except VisaRuleVersion.DoesNotExist:
            _previous_is_published[instance.pk] = False


@receiver(post_save, sender=VisaRuleVersion)
def handle_rule_version_published(sender, instance, created, **kwargs):
    """
    Signal handler for rule version publishing.
    - Notifies users with active cases for the affected visa type
    - Sends email notifications
    """
    # Trigger when a rule version is published (either on creation with is_published=True or when is_published changes to True)
    was_published = _previous_is_published.get(instance.pk, False) if not created else False
    is_now_published = instance.is_published
    
    # Clean up tracking
    if instance.pk in _previous_is_published:
        del _previous_is_published[instance.pk]
    
    # Only notify if rule was just published (not if it was already published)
    if is_now_published and not was_published:
        # New rule version published - notify users with active cases
        try:
            # Get all active cases for this visa type's jurisdiction
            active_cases = CaseSelector.get_by_jurisdiction(instance.visa_type.jurisdiction)
            
            # Filter cases that might be affected (status not closed)
            affected_cases = active_cases.exclude(status='closed')
            
            notified_count = 0
            for case in affected_cases:
                # Check user settings to see if they want rule change notifications
                try:
                    user_settings = case.user.user_settings
                    if user_settings.notify_rule_changes:
                        # Create in-app notification
                        NotificationService.create_notification(
                            user_id=str(case.user.id),
                            notification_type='rule_change',
                            title=f'Immigration Rules Updated: {instance.visa_type.name}',
                            message=f'Rules for {instance.visa_type.name} have been updated. You may want to re-check your eligibility.',
                            priority='medium',
                            related_entity_type='visa_rule_version',
                            related_entity_id=str(instance.id),
                            metadata={
                                'visa_type_id': str(instance.visa_type.id),
                                'visa_type_name': instance.visa_type.name,
                                'version_number': instance.version_number
                            }
                        )
                        
                        # Send email notification (async via Celery)
                        send_rule_change_notification_email_task.delay(
                            user_id=str(case.user.id),
                            visa_type_id=str(instance.visa_type.id),
                            rule_version_id=str(instance.id)
                        )
                        notified_count += 1
                except Exception as e:
                    logger.warning(f"Error notifying user {case.user.id} about rule change: {e}")
                    continue
            
            logger.info(f"Notified {notified_count} users about rule change for {instance.visa_type.name}")
            
        except Exception as e:
            logger.error(f"Error handling rule version publication: {e}")

