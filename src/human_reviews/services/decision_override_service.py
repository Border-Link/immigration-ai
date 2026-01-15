import logging
from typing import Optional
from django.db import transaction
from main_system.utils.cache_utils import cache_result, invalidate_cache
from human_reviews.models.decision_override import DecisionOverride
from human_reviews.repositories.decision_override_repository import DecisionOverrideRepository
from human_reviews.selectors.decision_override_selector import DecisionOverrideSelector
from human_reviews.selectors.review_selector import ReviewSelector
from immigration_cases.selectors.case_selector import CaseSelector
from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
from ai_decisions.models.eligibility_result import EligibilityResult
from immigration_cases.services.case_service import CaseService
from human_reviews.services.review_note_service import ReviewNoteService
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "decision_overrides"


class DecisionOverrideService:
    """Service for DecisionOverride business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda o: o is not None)
    def create_decision_override(case_id: str, original_result_id: str, overridden_outcome: str,
                               reason: str, reviewer_id: str = None, review_id: str = None) -> Optional[DecisionOverride]:
        """
        Create a decision override following the workflow from implementation.md.
        
        Requires: Case must have a completed payment before decision overrides can be created.
        
        Steps:
        1. Validate input
        2. Store override
        3. Add review note
        4. Update review status
        5. Update case status
        6. Log audit event
        
        All steps are wrapped in a transaction to ensure atomicity.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            with transaction.atomic():
                # Step 1: Validate input
                case = CaseSelector.get_by_id(case_id)
                if not case:
                    logger.error(f"Case {case_id} not found")
                    return None
                
                # Validate payment requirement
                is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="decision override creation")
                if not is_valid:
                    logger.warning(f"Decision override creation blocked for case {case_id}: {error}")
                    raise ValidationError(error)
                original_result = EligibilityResultSelector.get_by_id(original_result_id)
                
                # Verify original result belongs to the case
                if original_result.case.id != case.id:
                    logger.error(f"Eligibility result {original_result_id} does not belong to case {case_id}")
                    return None
                
                # Validate outcome
                valid_outcomes = [choice[0] for choice in EligibilityResult.OUTCOME_CHOICES]
                if overridden_outcome not in valid_outcomes:
                    logger.error(f"Invalid overridden_outcome: {overridden_outcome}")
                    return None
                
                reviewer = None
                if reviewer_id:
                    from users_access.selectors.user_selector import UserSelector
                    reviewer = UserSelector.get_by_id(reviewer_id)
                    # Verify reviewer has reviewer role AND is staff or admin
                    if reviewer.role != 'reviewer':
                        logger.error(f"User {reviewer_id} does not have reviewer role")
                        return None
                    if not (reviewer.is_staff or reviewer.is_superuser):
                        logger.error(f"User {reviewer_id} is not staff or admin")
                        return None
                
                # Step 2: Store override
                override = DecisionOverrideRepository.create_decision_override(
                    case=case,
                    original_result=original_result,
                    overridden_outcome=overridden_outcome,
                    reason=reason,
                    reviewer=reviewer
                )
                
                # Step 3: Add review note (if review_id provided)
                if review_id:
                    try:
                        review = ReviewSelector.get_by_id(review_id)
                        ReviewNoteService.create_review_note(
                            review_id=review_id,
                            note=f"Override created: {reason}",
                            is_internal=False
                        )
                        
                        # Step 4: Update review status
                        from human_reviews.services.review_service import ReviewService
                        ReviewService.complete_review(review_id)
                    except Exception as e:
                        logger.warning(f"Error adding review note or updating review: {e}")
                
                # Step 5: Update case status
                CaseService.update_case(case_id, status='reviewed')
                
                # Step 6: Log audit event
                try:
                    AuditLogService.create_audit_log(
                        level='INFO',
                        logger_name='decision_override',
                        message=f"Decision override created for case {case_id}",
                        pathname=None,
                        lineno=None,
                        func_name='create_decision_override',
                        process=None,
                        thread=None
                    )
                except Exception as audit_error:
                    logger.warning(f"Failed to create audit log: {audit_error}")
                    # Don't fail the transaction if audit logging fails
                
                return override
        except Exception as e:
            logger.error(f"Error creating decision override: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")  # 5 minutes - overrides change when reviewers make decisions
    def get_all():
        """Get all decision overrides."""
        try:
            return DecisionOverrideSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all decision overrides: {e}")
            return DecisionOverride.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache overrides by case
    def get_by_case(case_id: str):
        """Get overrides by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return DecisionOverrideSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching overrides for case {case_id}: {e}")
            return DecisionOverride.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['original_result_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache overrides by result
    def get_by_original_result(original_result_id: str):
        """Get overrides by original eligibility result."""
        try:
            original_result = EligibilityResultSelector.get_by_id(original_result_id)
            return DecisionOverrideSelector.get_by_original_result(original_result)
        except Exception as e:
            logger.error(f"Error fetching overrides for result {original_result_id}: {e}")
            return DecisionOverride.objects.none()

    @staticmethod
    @cache_result(timeout=300, keys=['original_result_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache latest override by result
    def get_latest_by_original_result(original_result_id: str) -> Optional[DecisionOverride]:
        """Get latest override for an eligibility result."""
        try:
            original_result = EligibilityResultSelector.get_by_id(original_result_id)
            return DecisionOverrideSelector.get_latest_by_original_result(original_result)
        except EligibilityResult.DoesNotExist:
            logger.error(f"Eligibility result {original_result_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching latest override for result {original_result_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=['reviewer_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache overrides by reviewer
    def get_by_reviewer(reviewer_id: str):
        """Get overrides by reviewer."""
        try:
            from users_access.selectors.user_selector import UserSelector
            reviewer = UserSelector.get_by_id(reviewer_id)
            return DecisionOverrideSelector.get_by_reviewer(reviewer)
        except Exception as e:
            logger.error(f"Error fetching overrides for reviewer {reviewer_id}: {e}")
            return DecisionOverride.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['override_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache override by ID
    def get_by_id(override_id: str) -> Optional[DecisionOverride]:
        """Get decision override by ID."""
        try:
            return DecisionOverrideSelector.get_by_id(override_id)
        except DecisionOverride.DoesNotExist:
            logger.error(f"Decision override {override_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching decision override {override_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda o: o is not None)
    def update_decision_override(override_id: str, **fields) -> Optional[DecisionOverride]:
        """
        Update decision override fields.
        
        Requires: Case must have a completed payment before decision overrides can be updated.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            override = DecisionOverrideSelector.get_by_id(override_id)
            if not override:
                logger.error(f"Decision override {override_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(
                override.case, 
                operation_name="decision override update"
            )
            if not is_valid:
                logger.warning(f"Decision override update blocked for case {override.case.id}: {error}")
                raise ValidationError(error)
            
            return DecisionOverrideRepository.update_decision_override(override, **fields)
        except DecisionOverride.DoesNotExist:
            logger.error(f"Decision override {override_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating decision override {override_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_decision_override(override_id: str) -> bool:
        """
        Delete a decision override.
        
        Requires: Case must have a completed payment before decision overrides can be deleted.
        This prevents abuse and ensures only paid cases can manage their decision overrides.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            override = DecisionOverrideSelector.get_by_id(override_id)
            if not override:
                logger.error(f"Decision override {override_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(
                override.case, 
                operation_name="decision override deletion"
            )
            if not is_valid:
                logger.warning(f"Decision override deletion blocked for case {override.case.id}: {error}")
                raise ValidationError(error)
            
            DecisionOverrideRepository.delete_decision_override(override)
            return True
        except DecisionOverride.DoesNotExist:
            logger.error(f"Decision override {override_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting decision override {override_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(case_id=None, reviewer_id=None, original_result_id=None, overridden_outcome=None, date_from=None, date_to=None):
        """Get decision overrides with advanced filtering for admin."""
        try:
            return DecisionOverrideSelector.get_by_filters(
                case_id=case_id,
                reviewer_id=reviewer_id,
                original_result_id=original_result_id,
                overridden_outcome=overridden_outcome,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering decision overrides: {e}")
            return DecisionOverride.objects.none()
