"""
Payment Repository

Write operations for Payment model.
All database write operations must live here.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from payments.models.payment import Payment
from payments.helpers.status_validator import PaymentStatusTransitionValidator
from payments.helpers.payment_validator import PaymentValidator
from immigration_cases.models.case import Case


class PaymentRepository:
    """Repository for Payment write operations."""

    @staticmethod
    def create_payment(
        case: Case,
        amount,
        currency: str = Payment.DEFAULT_CURRENCY,
        status: str = 'pending',
        payment_provider: str = None,
        provider_transaction_id: str = None,
        purpose: str = 'case_fee',
        plan: str = None,
    ) -> Payment:
        """
        Create a new payment.
        
        Args:
            case: Case instance
            amount: Payment amount
            currency: Currency code (default: USD)
            status: Payment status
            payment_provider: Payment provider name
            provider_transaction_id: Transaction ID from provider
            
        Returns:
            Created Payment instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate currency
        if currency not in [code for code, _ in Payment.SUPPORTED_CURRENCIES]:
            currency = Payment.DEFAULT_CURRENCY
        
        # Ensure one payment per case for the given purpose (prevents duplicate base payments)
        is_valid, error = PaymentValidator.ensure_one_payment_per_case(case, purpose=purpose)
        if not is_valid:
            raise ValidationError(error)

        if purpose == "case_fee" and not plan:
            raise ValidationError("Plan is required for case_fee payments.")
        
        with transaction.atomic():
            payment = Payment.objects.create(
                user=case.user,
                case=case,
                amount=amount,
                currency=currency,
                status=status,
                payment_provider=payment_provider,
                provider_transaction_id=provider_transaction_id,
                purpose=purpose,
                plan=plan if purpose == 'case_fee' else None,
            )
            payment.full_clean()
            payment.save()
            return payment

    @staticmethod
    def create_user_payment(
        user,
        amount,
        currency: str = Payment.DEFAULT_CURRENCY,
        status: str = 'pending',
        payment_provider: str = None,
        provider_transaction_id: str = None,
        purpose: str = 'case_fee',
        plan: str = None,
    ) -> Payment:
        """
        Create a pre-case payment for a user (case is nullable).
        """
        # Validate currency
        if currency not in [code for code, _ in Payment.SUPPORTED_CURRENCIES]:
            currency = Payment.DEFAULT_CURRENCY

        # Only base case fee payments are allowed as "pre-case" payments (case must be attached later).
        if purpose != 'case_fee':
            raise ValidationError("Only case_fee payments can be created without a case.")
        if not plan:
            raise ValidationError("Plan is required for case_fee payments.")

        with transaction.atomic():
            payment = Payment.objects.create(
                user=user,
                case=None,
                amount=amount,
                currency=currency,
                status=status,
                payment_provider=payment_provider,
                provider_transaction_id=provider_transaction_id,
                purpose=purpose,
                plan=plan if purpose == 'case_fee' else None,
            )
            payment.full_clean()
            payment.save()
            return payment

    @staticmethod
    def update_payment(payment: Payment, version: int = None, **fields) -> Payment:
        """
        Update payment fields with optimistic locking support and status transition validation.
        
        Args:
            payment: Payment instance to update
            version: Expected version for optimistic locking (optional)
            **fields: Fields to update
            
        Returns:
            Updated Payment instance
            
        Raises:
            ValidationError: If version mismatch, invalid status transition, or validation fails
        """
        with transaction.atomic():
            # Optimistic locking check
            if version is not None:
                current_version = Payment.objects.filter(id=payment.id).values_list('version', flat=True).first()
                if current_version != version:
                    raise ValidationError(
                        f"Payment was modified by another user. Expected version {version}, got {current_version}"
                    )
            
            # Validate status transition if status is being updated
            if 'status' in fields:
                is_valid, error = PaymentStatusTransitionValidator.validate_transition(
                    payment.status,
                    fields['status']
                )
                if not is_valid:
                    raise ValidationError(error)
            
            # Increment version atomically
            Payment.objects.filter(id=payment.id).update(version=F('version') + 1)
            payment.refresh_from_db()
            
            # Update fields (excluding version which is already updated)
            for key, value in fields.items():
                if hasattr(payment, key) and key != 'version':
                    setattr(payment, key, value)
            
            payment.full_clean()
            payment.save()
            return payment

    @staticmethod
    def delete_payment(payment: Payment) -> None:
        """
        Hard delete a payment (use soft_delete_payment for soft delete).
        
        Args:
            payment: Payment instance to delete
        """
        with transaction.atomic():
            # Store values before deletion for cache invalidation
            payment_id = payment.id
            case_id = payment.case.id if payment.case_id else None
            status = payment.status
            transaction_id = payment.provider_transaction_id
            
            payment.delete()
    
    @staticmethod
    def soft_delete_payment(payment: Payment, deleted_by=None) -> Payment:
        """
        Soft delete a payment.
        
        Args:
            payment: Payment instance to soft delete
            deleted_by: User performing the deletion
            
        Returns:
            Soft-deleted Payment instance
        """
        with transaction.atomic():
            # IMPORTANT: persist is_deleted/deleted_at in the DB before refreshing,
            # otherwise refresh_from_db() will overwrite in-memory changes.
            Payment.objects.filter(id=payment.id).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                version=F('version') + 1,
            )
            payment.refresh_from_db()
            return payment
    
    @staticmethod
    def restore_payment(payment: Payment, restored_by=None) -> Payment:
        """
        Restore a soft-deleted payment.
        
        Args:
            payment: Payment instance to restore
            restored_by: User performing the restoration
            
        Returns:
            Restored Payment instance
        """
        with transaction.atomic():
            Payment.objects.filter(id=payment.id).update(
                is_deleted=False,
                deleted_at=None,
                version=F('version') + 1,
            )
            payment.refresh_from_db()
            return payment