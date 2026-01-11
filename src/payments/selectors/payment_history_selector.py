"""
Payment History Selector

Handles all read operations for PaymentHistory model.
"""
from payments.models.payment_history import PaymentHistory
from typing import List, Optional


class PaymentHistorySelector:
    """Selector for PaymentHistory read operations."""
    
    @staticmethod
    def get_by_payment(payment_id: str) -> List[PaymentHistory]:
        """
        Get all history entries for a payment.
        
        Args:
            payment_id: UUID of the payment
            
        Returns:
            List of PaymentHistory instances ordered by created_at (newest first)
        """
        return list(
            PaymentHistory.objects
            .filter(payment_id=payment_id)
            .select_related('payment', 'changed_by')
            .order_by('-created_at')
        )
    
    @staticmethod
    def get_by_event_type(event_type: str, limit: int = 100) -> List[PaymentHistory]:
        """
        Get history entries by event type.
        
        Args:
            event_type: Event type to filter by
            limit: Maximum number of results
            
        Returns:
            List of PaymentHistory instances
        """
        return list(
            PaymentHistory.objects
            .filter(event_type=event_type)
            .select_related('payment', 'changed_by')
            .order_by('-created_at')[:limit]
        )
    
    @staticmethod
    def get_recent_by_payment(payment_id: str, limit: int = 10) -> List[PaymentHistory]:
        """
        Get recent history entries for a payment.
        
        Args:
            payment_id: UUID of the payment
            limit: Maximum number of results
            
        Returns:
            List of PaymentHistory instances
        """
        return list(
            PaymentHistory.objects
            .filter(payment_id=payment_id)
            .select_related('payment', 'changed_by')
            .order_by('-created_at')[:limit]
        )
