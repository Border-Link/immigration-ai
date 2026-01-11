from celery import shared_task
import logging
from emails.send import SendEmailService
from main_system.utils.tasks_base import BaseTaskWithMeta
from users_access.selectors.user_selector import UserSelector
from users_access.selectors.user_profile_selector import UserProfileSelector
from immigration_cases.selectors.case_selector import CaseSelector
from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
from human_reviews.selectors.review_selector import ReviewSelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_case_status_update_email_task(self, user_id: str, case_id: str, status: str, previous_status: str = None):
    """Send email notification for case status update."""
    try:
        user = UserSelector.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found for case status email")
            return
        
        try:
            profile = UserProfileSelector.get_by_user(user)
            first_name = profile.first_name if profile and profile.first_name else user.email.split('@')[0]
        except Exception:
            first_name = user.email.split('@')[0]
        
        case = CaseSelector.get_by_id(case_id)
        if not case:
            logger.error(f"Case {case_id} not found for status email")
            return
        
        status_messages = {
            'draft': 'Your case is in draft status.',
            'evaluated': 'Your case has been evaluated. Check your eligibility results.',
            'awaiting_review': 'Your case is awaiting human review.',
            'reviewed': 'Your case has been reviewed by our team.',
            'closed': 'Your case has been closed.',
        }
        
        message = status_messages.get(status, f'Your case status has been updated to {status}.')
        
        context = {
            'first_name': first_name,
            'case_id': str(case.id),
            'status': status,
            'previous_status': previous_status,
            'message': message,
        }
        
        SendEmailService().send_mail(
            subject=f'Case Status Update: {status.title()}',
            template_name='emails/case_status_update.html',
            context=context,
            recipient_list=[user.email]
        )
        
        logger.info(f"Case status update email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except Exception as e:
        logger.error(f"Error sending case status email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_eligibility_result_email_task(self, user_id: str, eligibility_result_id: str, outcome: str, confidence: float):
    """Send email notification for eligibility result."""
    try:
        user = UserSelector.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found for eligibility result email")
            return
        
        try:
            profile = UserProfileSelector.get_by_user(user)
            first_name = profile.first_name if profile and profile.first_name else user.email.split('@')[0]
        except Exception:
            first_name = user.email.split('@')[0]
        
        result = EligibilityResultSelector.get_by_id(eligibility_result_id)
        if not result:
            logger.error(f"Eligibility result {eligibility_result_id} not found")
            return
        
        context = {
            'first_name': first_name,
            'visa_type': result.visa_type.name,
            'outcome': outcome,
            'confidence': confidence,
            'case_id': str(result.case.id),
        }
        
        SendEmailService().send_mail(
            subject=f'Eligibility Result: {result.visa_type.name} - {outcome.title()}',
            template_name='emails/eligibility_result.html',
            context=context,
            recipient_list=[user.email]
        )
        
        logger.info(f"Eligibility result email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except Exception as e:
        logger.error(f"Error sending eligibility result email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_review_assignment_email_task(self, reviewer_id: str, review_id: str, case_id: str):
    """Send email notification for review assignment."""
    try:
        reviewer = UserSelector.get_by_id(reviewer_id)
        if not reviewer:
            logger.error(f"Reviewer {reviewer_id} not found for review assignment email")
            return
        
        review = ReviewSelector.get_by_id(review_id)
        if not review:
            logger.error(f"Review {review_id} not found")
            return
        
        context = {
            'reviewer_email': reviewer.email,
            'case_id': case_id,
            'review_id': review_id,
            'priority': getattr(review, 'priority', 'medium'),
        }
        
        SendEmailService().send_mail(
            subject='New Review Assignment',
            template_name='emails/review_assignment.html',
            context=context,
            recipient_list=[reviewer.email]
        )
        
        logger.info(f"Review assignment email sent to {reviewer.email}")
        return {'status': 'success', 'email': reviewer.email}
        
    except Exception as e:
        logger.error(f"Error sending review assignment email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_review_completed_email_task(self, user_id: str, review_id: str, case_id: str):
    """Send email notification when review is completed."""
    try:
        user = UserSelector.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found for review completed email")
            return
        
        try:
            profile = UserProfileSelector.get_by_user(user)
            first_name = profile.first_name if profile and profile.first_name else user.email.split('@')[0]
        except Exception:
            first_name = user.email.split('@')[0]
        
        context = {
            'first_name': first_name,
            'case_id': case_id,
            'review_id': review_id,
        }
        
        SendEmailService().send_mail(
            subject='Case Review Completed',
            template_name='emails/review_completed.html',
            context=context,
            recipient_list=[user.email]
        )
        
        logger.info(f"Review completed email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except Exception as e:
        logger.error(f"Error sending review completed email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_document_status_email_task(self, user_id: str, document_id: str, check_type: str, result: str, details: str = None):
    """Send email notification for document status."""
    try:
        user = UserSelector.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found for document status email")
            return
        
        try:
            profile = UserProfileSelector.get_by_user(user)
            first_name = profile.first_name if profile and profile.first_name else user.email.split('@')[0]
        except Exception:
            first_name = user.email.split('@')[0]
        
        document = CaseDocumentSelector.get_by_id(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        context = {
            'first_name': first_name,
            'document_id': document_id,
            'check_type': check_type,
            'result': result,
            'details': details or '',
            'case_id': str(document.case.id),
        }
        
        subject = 'Document Check Failed' if result == 'fail' else 'Document Status Update'
        
        SendEmailService().send_mail(
            subject=subject,
            template_name='emails/document_status.html',
            context=context,
            recipient_list=[user.email]
        )
        
        logger.info(f"Document status email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except Exception as e:
        logger.error(f"Error sending document status email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_rule_validation_task_email_task(self, reviewer_id: str, task_id: str):
    """Send email notification for rule validation task assignment."""
    try:
        reviewer = UserSelector.get_by_id(reviewer_id)
        if not reviewer:
            logger.error(f"Reviewer {reviewer_id} not found for rule validation task email")
            return
        
        task = RuleValidationTaskSelector.get_by_id(task_id)
        if not task:
            logger.error(f"Rule validation task {task_id} not found")
            return
        
        context = {
            'reviewer_email': reviewer.email,
            'task_id': task_id,
            'parsed_rule_id': str(task.parsed_rule.id) if task.parsed_rule else None,
        }
        
        SendEmailService().send_mail(
            subject='New Rule Validation Task Assigned',
            template_name='emails/rule_validation_task.html',
            context=context,
            recipient_list=[reviewer.email]
        )
        
        logger.info(f"Rule validation task email sent to {reviewer.email}")
        return {'status': 'success', 'email': reviewer.email}
        
    except Exception as e:
        logger.error(f"Error sending rule validation task email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def send_rule_change_notification_email_task(self, user_id: str, visa_type_id: str, rule_version_id: str):
    """Send email notification when rules change for a user's visa type."""
    try:
        user = UserSelector.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found for rule change email")
            return
        
        try:
            profile = UserProfileSelector.get_by_user(user)
            first_name = profile.first_name if profile and profile.first_name else user.email.split('@')[0]
        except Exception:
            first_name = user.email.split('@')[0]
        
        from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
        from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
        
        visa_type = VisaTypeSelector.get_by_id(visa_type_id)
        rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
        
        if not visa_type or not rule_version:
            logger.error(f"Visa type or rule version not found")
            return
        
        context = {
            'first_name': first_name,
            'visa_type': visa_type.name,
            'rule_version': rule_version.version_number,
        }
        
        SendEmailService().send_mail(
            subject=f'Immigration Rules Updated: {visa_type.name}',
            template_name='emails/rule_change.html',
            context=context,
            recipient_list=[user.email]
        )
        
        logger.info(f"Rule change email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except Exception as e:
        logger.error(f"Error sending rule change email: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

