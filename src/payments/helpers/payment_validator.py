"""
Payment Validator

Validates payment requirements for case operations.
Production-ready with caching, logging, and comprehensive validation.
"""
import logging
from typing import Tuple, Optional
from payments.models.payment import Payment
from payments.selectors.payment_selector import PaymentSelector
from payments.selectors.pricing_selector import PricingSelector
from immigration_cases.models.case import Case
from main_system.utils.cache_utils import (
    bump_namespace,
    cache_get,
    cache_set,
    get_namespace_version,
    make_cache_key,
)

logger = logging.getLogger('django')


class PaymentValidator:
    """Validator for payment requirements."""

    @staticmethod
    def _case_payment_validation_namespace(case_id: str) -> str:
        return f"payment_validation:completed_payment:case:{case_id}"

    @staticmethod
    def _case_payment_validation_cache_key(case_id: str) -> str:
        ns = PaymentValidator._case_payment_validation_namespace(case_id)
        return make_cache_key(
            namespace=ns,
            namespace_version=get_namespace_version(ns),
            func_qualname="payments.payment_validator.has_completed_payment_for_case",
            user_scope="global",
            user_id="global",
            key_material={"case_id": str(case_id)},
        )
    
    @staticmethod
    def has_completed_payment_for_case(case: Case, use_cache: bool = True) -> Tuple[bool, Optional[Payment]]:
        """
        Check if case has a completed payment.
        
        Uses caching for performance in production.
        
        Args:
            case: Case instance
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Tuple of (has_completed_payment, payment_instance)
        """
        if not case:
            return False, None
        
        # Check cache first
        if use_cache:
            cache_key = PaymentValidator._case_payment_validation_cache_key(str(case.id))
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                # Cache stores (has_payment, payment_id) or None
                if cached_result:
                    has_payment, payment_id = cached_result
                    if has_payment:
                        try:
                            payment = PaymentSelector.get_completed_case_fee_by_id(payment_id)
                            if payment:
                                return True, payment
                        except Exception:
                            # Cache invalid, bump namespace to invalidate this case's cached result.
                            bump_namespace(PaymentValidator._case_payment_validation_namespace(str(case.id)))
                    else:
                        return False, None
        
        # Query database
        payments = PaymentSelector.get_by_case(case)
        completed_payment = payments.filter(status='completed', is_deleted=False, purpose='case_fee').first()
        
        # Cache result
        if use_cache:
            cache_key = PaymentValidator._case_payment_validation_cache_key(str(case.id))
            if completed_payment:
                cache_set(cache_key, (True, str(completed_payment.id)), timeout=300)  # 5 minutes
            else:
                cache_set(cache_key, (False, None), timeout=60)  # 1 minute for negative cache
        
        if completed_payment:
            return True, completed_payment
        return False, None

    @staticmethod
    def get_case_fee_plan_for_case(case: Case) -> Optional[str]:
        """
        Return the plan associated with the completed case fee payment for this case.

        Returns:
            'basic' | 'special' | 'big' | None (if no completed case fee payment)
        """
        ok, payment = PaymentValidator.has_completed_payment_for_case(case, use_cache=True)
        if not ok or not payment:
            return None
        return payment.plan

    @staticmethod
    def validate_case_has_ai_calls_entitlement(case: Case, operation_name: str = "AI calls") -> Tuple[bool, Optional[str]]:
        """
        AI calls entitlement:
        - requires a completed case fee payment, AND
        - plan includes_ai_calls (admin-configured), OR
        - ai_calls_addon payment is completed for the case.
        """
        # Always require base case payment for any entitlement.
        has_payment, _payment = PaymentValidator.has_completed_payment_for_case(case, use_cache=True)
        if not has_payment:
            return False, f"Case requires a completed payment before {operation_name} can be performed."

        plan = PaymentValidator.get_case_fee_plan_for_case(case)
        if plan:
            try:
                item = PricingSelector.get_items(kind="plan", is_active=True).filter(code=plan).first()
                if item and item.includes_ai_calls:
                    return True, None
            except Exception:
                pass

        # Allow AI calls via add-on
        try:
            payments = PaymentSelector.get_by_case(case)
            addon = payments.filter(status="completed", is_deleted=False, purpose="ai_calls_addon").first()
            if addon:
                return True, None
        except Exception:
            pass
        return (
            False,
            f"Case does not have AI calls entitlement. Purchase AI calls add-on or a plan with AI calls before {operation_name} can be performed.",
        )
    
    @staticmethod
    def has_completed_payment_for_user(user_id: str) -> Tuple[bool, Optional[Payment]]:
        """
        Check if user has any completed payment.
        
        This is useful for checking if user can create a new case.
        
        Args:
            user_id: User UUID
            
        Returns:
            Tuple of (has_completed_payment, payment_instance)
        """
        from immigration_cases.selectors.case_selector import CaseSelector
        from users_access.selectors.user_selector import UserSelector
        
        # Get user
        user = UserSelector.get_by_id(user_id)
        if not user:
            return False, None
        
        # Get all cases for user
        user_cases = CaseSelector.get_by_user(user)
        
        # Check each case for completed payment
        for case in user_cases:
            has_payment, payment = PaymentValidator.has_completed_payment_for_case(case)
            if has_payment:
                return True, payment
        
        return False, None

    @staticmethod
    def has_unassigned_completed_payment_for_user(user_id: str) -> Tuple[bool, Optional[Payment]]:
        """
        Check if user has a completed payment not yet attached to a case.

        This supports the "payment required before case creation" flow.
        """
        from users_access.selectors.user_selector import UserSelector

        user = UserSelector.get_by_id(user_id)
        if not user:
            return False, None

        unassigned = PaymentSelector.get_unassigned_completed_by_user(user)
        payment = unassigned.first()
        if payment:
            return True, payment
        return False, None
    
    @staticmethod
    def validate_case_has_payment(case: Case, operation_name: str = "operation") -> Tuple[bool, Optional[str]]:
        """
        Validate that case has a completed payment.
        
        Production-ready validation with detailed error messages and logging.
        
        Args:
            case: Case instance
            operation_name: Name of the operation being validated (for logging)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not case:
            error = "Invalid case provided for payment validation."
            logger.error(f"Payment validation failed: {error}")
            return False, error
        
        has_payment, payment = PaymentValidator.has_completed_payment_for_case(case, use_cache=True)
        
        if not has_payment:
            error = f"Case requires a completed payment before {operation_name} can be performed. Please complete your payment first."
            logger.warning(f"Payment validation failed for case {case.id}, operation: {operation_name}")
            return False, error
        
        # Double-check payment status (should already be 'completed' from query, but verify)
        if payment.status != 'completed':
            error = f"Payment status is '{payment.status}'. Payment must be completed before {operation_name} can be performed."
            logger.warning(f"Payment validation failed for case {case.id}: payment {payment.id} status is {payment.status}")
            return False, error
        
        # Verify payment is not deleted
        if payment.is_deleted:
            error = f"Payment has been deleted. Please create a new payment before {operation_name} can be performed."
            logger.warning(f"Payment validation failed for case {case.id}: payment {payment.id} is deleted")
            return False, error
        
        logger.debug(f"Payment validation passed for case {case.id}, payment {payment.id}, operation: {operation_name}")
        return True, None
    
    @staticmethod
    def can_create_case_for_user(user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can create a new case.
        
        For now, we allow case creation but require payment before case operations.
        Alternatively, you can require payment before case creation.
        
        Args:
            user_id: User UUID
            
        Returns:
            Tuple of (can_create, error_message)
        """
        # Require payment before case creation:
        # user must have a completed payment which is not yet attached to a case.
        has_payment, _payment = PaymentValidator.has_unassigned_completed_payment_for_user(user_id)
        if not has_payment:
            return (
                False,
                "You must have a completed payment before creating a case. Please complete your payment first.",
            )
        return True, None
    
    @staticmethod
    def ensure_one_payment_per_case(case: Case, purpose: str = 'case_fee') -> Tuple[bool, Optional[str]]:
        """
        Ensure only one active payment per case for the given purpose.

        - For `case_fee`: enforce exactly one completed payment per case (the base case payment).
        - For `reviewer_addon`: allow at most one completed add-on per case (and prevent multiple concurrent pending add-ons).
        """
        if not case:
            return True, None

        payments = PaymentSelector.get_by_case(case).filter(purpose=purpose)

        # Count non-deleted, non-refunded payments for this purpose
        active_payments = payments.exclude(status='refunded').exclude(is_deleted=True)
        completed_payments = active_payments.filter(status='completed')

        if completed_payments.exists():
            completed_count = completed_payments.count()
            logger.warning(
                f"Attempt to create duplicate payment for case {case.id} (purpose={purpose}). "
                f"Existing completed payments: {completed_count}"
            )
            if purpose == 'case_fee':
                return (
                    False,
                    "Case already has a completed case fee payment. Only one case fee payment per case is allowed.",
                )
            return (
                False,
                "Case already has a completed reviewer add-on payment. Only one reviewer add-on per case is allowed.",
            )

        pending_payments = active_payments.filter(status__in=['pending', 'processing'])
        if pending_payments.count() > 1:
            logger.warning(
                f"Multiple pending payments detected for case {case.id} (purpose={purpose}). "
                f"Count: {pending_payments.count()}"
            )
            return (
                False,
                "Multiple pending payments detected for this case. Please complete or cancel your existing payment before creating a new one.",
            )

        return True, None

    @staticmethod
    def has_completed_reviewer_addon_for_case(case: Case) -> Tuple[bool, Optional[Payment]]:
        """Check if case has a completed reviewer add-on payment."""
        if not case:
            return False, None
        payments = PaymentSelector.get_by_case(case)
        addon = payments.filter(status='completed', is_deleted=False, purpose='reviewer_addon').first()
        if addon:
            return True, addon
        return False, None

    @staticmethod
    def validate_case_has_human_review_entitlement(case: Case, operation_name: str = "operation") -> Tuple[bool, Optional[str]]:
        """
        Human review entitlement:
        - requires a completed case fee payment, AND
        - plan includes_human_review (admin-configured), OR
        - reviewer_addon payment is completed for the case.
        """
        if not case:
            error = "Invalid case provided for human review entitlement validation."
            logger.error(f"Reviewer add-on payment validation failed: {error}")
            return False, error

        has_payment, _payment = PaymentValidator.has_completed_payment_for_case(case, use_cache=True)
        if not has_payment:
            return False, f"Case requires a completed payment before {operation_name} can be performed."

        plan = PaymentValidator.get_case_fee_plan_for_case(case)
        if plan:
            try:
                item = PricingSelector.get_items(kind="plan", is_active=True).filter(code=plan).first()
                if item and item.includes_human_review:
                    return True, None
            except Exception:
                pass

        ok, addon_payment = PaymentValidator.has_completed_reviewer_addon_for_case(case)
        if not ok or not addon_payment:
            return (
                False,
                f"Case does not have human review entitlement. Purchase reviewer add-on or a plan with human review before {operation_name} can be performed.",
            )
        if addon_payment.is_deleted or addon_payment.status != 'completed':
            return (
                False,
                f"Reviewer add-on payment must be completed before {operation_name} can be performed.",
            )
        return True, None

    @staticmethod
    def validate_case_has_reviewer_addon(case: Case, operation_name: str = "operation") -> Tuple[bool, Optional[str]]:
        """
        Backwards-compatible alias.

        Prefer `validate_case_has_human_review_entitlement`.
        """
        return PaymentValidator.validate_case_has_human_review_entitlement(case, operation_name=operation_name)
    
    @staticmethod
    def invalidate_payment_cache(case_id: str) -> None:
        """
        Invalidate payment cache for a case.
        
        Call this when payment status changes to ensure cache consistency.
        
        Args:
            case_id: UUID of the case
        """
        bump_namespace(PaymentValidator._case_payment_validation_namespace(str(case_id)))
        logger.debug(f"Invalidated payment cache for case {case_id}")