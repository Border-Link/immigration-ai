"""
Payment Validator

Validates payment requirements for case operations.
Production-ready with caching, logging, and comprehensive validation.
"""
import logging
from typing import Tuple, Optional
from payments.models.payment import Payment
from payments.selectors.payment_selector import PaymentSelector
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
                            payment = Payment.objects.get(id=payment_id, status='completed', is_deleted=False)
                            return True, payment
                        except Payment.DoesNotExist:
                            # Cache invalid, bump namespace to invalidate this case's cached result.
                            bump_namespace(PaymentValidator._case_payment_validation_namespace(str(case.id)))
                    else:
                        return False, None
        
        # Query database
        payments = PaymentSelector.get_by_case(case)
        completed_payment = payments.filter(status='completed', is_deleted=False).first()
        
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
    def ensure_one_payment_per_case(case: Case) -> Tuple[bool, Optional[str]]:
        """
        Ensure only one active payment per case.
        
        Production-ready validation with comprehensive checks.
        
        Args:
            case: Case instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # For pre-case payments, case can be None (handled elsewhere).
        if not case:
            return True, None
        
        payments = PaymentSelector.get_by_case(case)
        
        # Count non-deleted, non-refunded payments
        active_payments = payments.exclude(status='refunded').exclude(is_deleted=True)
        completed_payments = active_payments.filter(status='completed')
        
        # If there's already a completed payment, don't allow another
        if completed_payments.exists():
            completed_count = completed_payments.count()
            logger.warning(f"Attempt to create duplicate payment for case {case.id}. Existing completed payments: {completed_count}")
            return False, "Case already has a completed payment. Only one payment per case is allowed. If you need to make another payment, please contact support."
        
        # Allow pending/processing payments (user might be retrying)
        # But prevent multiple pending payments
        pending_payments = active_payments.filter(status__in=['pending', 'processing'])
        pending_count = pending_payments.count()
        
        if pending_count > 1:
            logger.warning(f"Multiple pending payments detected for case {case.id}. Count: {pending_count}")
            return False, "Multiple pending payments detected. Please complete or cancel your existing payment before creating a new one."
        
        # Allow one pending/processing payment (for retry scenarios)
        return True, None
    
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