"""
Payment History Service

Business logic for payment history operations.
"""
import logging
from typing import List, Optional
from payments.models.payment import Payment
from payments.models.payment_history import PaymentHistory
from payments.repositories.payment_history_repository import PaymentHistoryRepository
from payments.selectors.payment_history_selector import PaymentHistorySelector

logger = logging.getLogger('django')


class PaymentHistoryService:
    """Service for PaymentHistory business logic."""
    
    @staticmethod
    def create_history_entry(
        payment: Payment,
        event_type: str,
        message: str,
        previous_status: str = None,
        new_status: str = None,
        metadata: dict = None,
        changed_by=None
    ) -> Optional[PaymentHistory]:
        """
        Create a payment history entry.
        
        Args:
            payment: Payment instance
            event_type: Type of event
            message: Event message
            previous_status: Previous payment status
            new_status: New payment status
            metadata: Additional metadata
            changed_by: User who triggered the event
            
        Returns:
            Created PaymentHistory instance or None on error
        """
        try:
            return PaymentHistoryRepository.create_history_entry(
                payment=payment,
                event_type=event_type,
                message=message,
                previous_status=previous_status,
                new_status=new_status,
                metadata=metadata or {},
                changed_by=changed_by
            )
        except Exception as e:
            logger.error(f"Error creating payment history entry: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_by_payment(payment_id: str) -> List[PaymentHistory]:
        """
        Get all history entries for a payment.
        
        Args:
            payment_id: UUID of the payment
            
        Returns:
            List of PaymentHistory instances
        """
        try:
            return PaymentHistorySelector.get_by_payment(payment_id)
        except Exception as e:
            logger.error(f"Error fetching payment history for {payment_id}: {e}", exc_info=True)
            return []
    
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
        try:
            return PaymentHistorySelector.get_recent_by_payment(payment_id, limit)
        except Exception as e:
            logger.error(f"Error fetching recent payment history for {payment_id}: {e}", exc_info=True)
            return []
