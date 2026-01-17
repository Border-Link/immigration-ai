from django.db.models.signals import post_save
from django.dispatch import receiver
from document_handling.models.case_document import CaseDocument
from document_handling.models.document_check import DocumentCheck
from users_access.services.notification_service import NotificationService
from users_access.tasks.email_tasks import send_document_status_email_task
from document_handling.tasks.document_tasks import process_document_task
import logging

logger = logging.getLogger('django')


@receiver(post_save, sender=CaseDocument)
def handle_document_uploaded(sender, instance, created, **kwargs):
    """
    Signal handler for document uploads.
    - Triggers async document processing (OCR, classification)
    - Sends notification to user
    """
    if created:
        # Document uploaded - trigger async processing
        try:
            process_document_task.delay(str(instance.id))
        except Exception as e:
            # In production this is queued async; in tests (eager) or if the broker is down,
            # avoid failing the upload transaction because processing can be retried later.
            logger.exception(f"Failed to enqueue process_document_task for document {instance.id}: {e}")
        
        # Send notification
        try:
            NotificationService.create_notification(
                user_id=str(instance.case.user.id),
                notification_type='document_status',
                title='Document Uploaded',
                message=f'Your document has been uploaded and is being processed.',
                priority='medium',
                related_entity_type='case_document',
                related_entity_id=str(instance.id),
                metadata={'case_id': str(instance.case.id)}
            )
        except Exception as e:
            logger.exception(f"Failed to create upload notification for document {instance.id}: {e}")


@receiver(post_save, sender=DocumentCheck)
def handle_document_check_result(sender, instance, created, **kwargs):
    """
    Signal handler for document check results.
    - Sends notification if check fails
    - Updates document status
    """
    if created:
        document = instance.case_document
        
        # If check failed, notify user
        if instance.result == 'failed':
            try:
                NotificationService.create_notification(
                    user_id=str(document.case.user.id),
                    notification_type='document_failed',
                    title='Document Check Failed',
                    message=f'Document check failed: {instance.check_type}. {instance.details or ""}',
                    priority='high',
                    related_entity_type='case_document',
                    related_entity_id=str(document.id),
                    metadata={
                        'check_type': instance.check_type,
                        'check_id': str(instance.id),
                        'case_id': str(document.case.id)
                    }
                )
            except Exception as e:
                logger.exception(f"Failed to create failure notification for document {document.id}: {e}")
            
            # Send email notification
            try:
                send_document_status_email_task.delay(
                    user_id=str(document.case.user.id),
                    document_id=str(document.id),
                    check_type=instance.check_type,
                    result=instance.result,
                    details=instance.details
                )
            except Exception as e:
                logger.exception(f"Failed to enqueue status email for document {document.id}: {e}")

