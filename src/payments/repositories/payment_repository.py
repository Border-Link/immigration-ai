"""
Payment Repository

Write operations for Payment model.
All database write operations must live here.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.cache import cache
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
        provider_transaction_id: str = None
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
        
        # Ensure one payment per case (prevent multiple completed payments)
        is_valid, error = PaymentValidator.ensure_one_payment_per_case(case)
        if not is_valid:
            raise ValidationError(error)
        
        with transaction.atomic():
            payment = Payment.objects.create(
                case=case,
                amount=amount,
                currency=currency,
                status=status,
                payment_provider=payment_provider,
                provider_transaction_id=provider_transaction_id
            )
            payment.full_clean()
            payment.save()
            
            # Invalidate cache
            cache.delete(f"payment:{payment.id}")
            cache.delete(f"payments:case:{case.id}")
            cache.delete("payments:all")
            cache.delete(f"payments:status:{status}")
            
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
            
            # Invalidate cache
            cache.delete(f"payment:{payment.id}")
            cache.delete(f"payments:case:{payment.case.id}")
            cache.delete("payments:all")
            cache.delete(f"payments:status:{payment.status}")
            if payment.provider_transaction_id:
                cache.delete(f"payments:transaction:{payment.provider_transaction_id}")
            
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
            case_id = payment.case.id
            status = payment.status
            transaction_id = payment.provider_transaction_id
            
            payment.delete()
            
            # Invalidate cache
            cache.delete(f"payment:{payment_id}")
            cache.delete(f"payments:case:{case_id}")
            cache.delete("payments:all")
            cache.delete(f"payments:status:{status}")
            if transaction_id:
                cache.delete(f"payments:transaction:{transaction_id}")
    
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
            payment.is_deleted = True
            payment.deleted_at = timezone.now()
            # Increment version
            Payment.objects.filter(id=payment.id).update(version=F('version') + 1)
            payment.refresh_from_db()
            payment.full_clean()
            payment.save()
            
            # Invalidate cache
            cache.delete(f"payment:{payment.id}")
            cache.delete(f"payments:case:{payment.case.id}")
            cache.delete("payments:all")
            cache.delete(f"payments:status:{payment.status}")
            if payment.provider_transaction_id:
                cache.delete(f"payments:transaction:{payment.provider_transaction_id}")
            
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
            payment.is_deleted = False
            payment.deleted_at = None
            # Increment version
            Payment.objects.filter(id=payment.id).update(version=F('version') + 1)
            payment.refresh_from_db()
            payment.full_clean()
            payment.save()
            
            # Invalidate cache
            cache.delete(f"payment:{payment.id}")
            cache.delete(f"payments:case:{payment.case.id}")
            cache.delete("payments:all")
            cache.delete(f"payments:status:{payment.status}")
            
            return payment