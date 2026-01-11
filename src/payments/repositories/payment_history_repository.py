"""
Payment History Repository

Handles all write operations for PaymentHistory model.
"""
from django.db import transaction
from payments.models.payment_history import PaymentHistory
from payments.models.payment import Payment


class PaymentHistoryRepository:
    """Repository for PaymentHistory write operations."""
    
    @staticmethod
    @transaction.atomic
    def create_history_entry(
        payment: Payment,
        event_type: str,
        message: str,
        previous_status: str = None,
        new_status: str = None,
        metadata: dict = None,
        changed_by=None
    ) -> PaymentHistory:
        """
        Create a new payment history entry.
        
        Args:
            payment: Payment instance
            event_type: Type of event
            message: Event message
            previous_status: Previous payment status (if status changed)
            new_status: New payment status (if status changed)
            metadata: Additional metadata
            changed_by: User who triggered the event
            
        Returns:
            Created PaymentHistory instance
        """
        history = PaymentHistory.objects.create(
            payment=payment,
            event_type=event_type,
            message=message,
            previous_status=previous_status,
            new_status=new_status,
            metadata=metadata or {},
            changed_by=changed_by
        )
        history.full_clean()
        history.save()
        return history
