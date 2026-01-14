"""
Payment Service

Business logic layer for payment operations.
All business logic must live here - no direct ORM access.
"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from payments.models.payment import Payment
from payments.repositories.payment_repository import PaymentRepository
from payments.selectors.payment_selector import PaymentSelector
from payments.services.payment_gateway_service import PaymentGatewayService
from payments.services.payment_history_service import PaymentHistoryService
from payments.services.payment_notification_service import PaymentNotificationService
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError
from payments.helpers.metrics import (
    track_payment_creation,
    track_payment_status_transition,
    track_payment_revenue,
    update_payments_by_status
)
from immigration_cases.selectors.case_selector import CaseSelector
from main_system.utils.cache_utils import cache_result
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')


class PaymentService:
    """Service for Payment business logic."""

    @staticmethod
    def create_payment(
        case_id: str,
        amount: Decimal,
        currency: str = Payment.DEFAULT_CURRENCY,
        status: str = 'pending',
        payment_provider: str = None,
        provider_transaction_id: str = None,
        changed_by=None
    ) -> Optional[Payment]:
        """
        Create a new payment.
        
        Args:
            case_id: UUID of the case
            amount: Payment amount
            currency: Currency code (default: USD)
            status: Payment status (default: pending)
            payment_provider: Payment provider name
            provider_transaction_id: Transaction ID from provider
            changed_by: User creating the payment
            
        Returns:
            Created Payment instance or None on error
        """
        try:
            case = CaseSelector.get_by_id(case_id)
            if not case:
                logger.error(f"Case {case_id} not found for payment creation")
                return None
            
            # Validate currency
            if currency not in [code for code, _ in Payment.SUPPORTED_CURRENCIES]:
                logger.warning(f"Unsupported currency {currency}, defaulting to {Payment.DEFAULT_CURRENCY}")
                currency = Payment.DEFAULT_CURRENCY
            
            payment = PaymentRepository.create_payment(
                case=case,
                amount=amount,
                currency=currency,
                status=status,
                payment_provider=payment_provider,
                provider_transaction_id=provider_transaction_id
            )
            
            # Track metrics
            track_payment_creation(currency, payment_provider or 'unknown', float(amount))
            
            # Create history entry
            PaymentHistoryService.create_history_entry(
                payment=payment,
                event_type='created',
                message=f"Payment created: {amount} {currency}",
                new_status=status,
                changed_by=changed_by
            )
            
            # Audit logging
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='payments',
                    message=f"Payment created: {payment.id} for case {case_id}, amount {amount} {currency}",
                    func_name='create_payment',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return payment
        except Exception as e:
            logger.error(f"Error creating payment: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - payment list changes frequently
    def get_all() -> QuerySet:
        """Get all payments."""
        return PaymentSelector.get_all()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'])  # 5 minutes - cache payments by case
    def get_by_case(case_id: str) -> QuerySet:
        """
        Get payments by case.
        
        Args:
            case_id: UUID of the case
            
        Returns:
            QuerySet of payments for the case
        """
        case = CaseSelector.get_by_id(case_id)
        if not case:
            return PaymentSelector.get_none()
        return PaymentSelector.get_by_case(case)

    @staticmethod
    @cache_result(timeout=300, keys=['status'])  # 5 minutes - cache payments by status
    def get_by_status(status: str) -> QuerySet:
        """
        Get payments by status.
        
        Args:
            status: Payment status
            
        Returns:
            QuerySet of payments with the status
        """
        return PaymentSelector.get_by_status(status)

    @staticmethod
    @cache_result(timeout=600, keys=['transaction_id'])  # 10 minutes - cache by transaction ID
    def get_by_provider_transaction_id(transaction_id: str) -> Optional[Payment]:
        """
        Get payment by provider transaction ID.
        
        Args:
            transaction_id: Provider transaction ID
            
        Returns:
            Payment instance or None
        """
        return PaymentSelector.get_by_provider_transaction_id(transaction_id)

    @staticmethod
    @cache_result(timeout=600, keys=['payment_id'])  # 10 minutes - cache payment by ID
    def get_by_id(payment_id: str) -> Optional[Payment]:
        """
        Get payment by ID.
        
        Args:
            payment_id: UUID of the payment
            
        Returns:
            Payment instance or None
        """
        try:
            return PaymentSelector.get_by_id(payment_id)
        except ObjectDoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching payment {payment_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def update_payment(
        payment_id: str,
        version: int = None,
        changed_by=None,
        reason: str = None,
        **fields
    ) -> Optional[Payment]:
        """
        Update payment fields.
        
        Args:
            payment_id: UUID of the payment
            version: Expected version for optimistic locking
            changed_by: User making the change
            reason: Reason for the update
            **fields: Fields to update
            
        Returns:
            Updated Payment instance or None on error
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for update")
                return None
            
            # Track status change
            previous_status = payment.status
            new_status = fields.get('status', payment.status)
            status_changed = previous_status != new_status
            
            updated_payment = PaymentRepository.update_payment(
                payment=payment,
                version=version,
                **fields
            )
            
            # Create history entry
            if status_changed:
                # Track status transition metrics
                track_payment_status_transition(previous_status, new_status)
                
                # Track revenue if completed
                if new_status == 'completed':
                    track_payment_revenue(updated_payment.currency, float(updated_payment.amount))
                    
                    # Invalidate payment cache when payment is completed
                    # This ensures case operations can immediately use the completed payment
                    from payments.helpers.payment_validator import PaymentValidator
                    PaymentValidator.invalidate_payment_cache(str(updated_payment.case.id))
                    logger.info(f"Payment {updated_payment.id} completed for case {updated_payment.case.id}, cache invalidated")
                
                # Update status gauge
                status_counts = PaymentSelector.get_statistics()
                for status_item in status_counts.get('status_breakdown', []):
                    update_payments_by_status(status_item['status'], status_item['count'])
                
                PaymentHistoryService.create_history_entry(
                    payment=updated_payment,
                    event_type='status_changed',
                    message=f"Payment status changed from {previous_status} to {new_status}" + (f": {reason}" if reason else ""),
                    previous_status=previous_status,
                    new_status=new_status,
                    metadata={'fields_updated': list(fields.keys()), 'reason': reason},
                    changed_by=changed_by
                )
                
                # Send notification
                notification_type = 'payment_completed' if new_status == 'completed' else \
                                   'payment_failed' if new_status == 'failed' else \
                                   'payment_refunded' if new_status == 'refunded' else \
                                   'status_changed'
                
                PaymentNotificationService.send_notification(
                    payment_id=str(updated_payment.id),
                    notification_type=notification_type,
                    previous_status=previous_status,
                    new_status=new_status
                )
            else:
                # Other field updates
                PaymentHistoryService.create_history_entry(
                    payment=updated_payment,
                    event_type='status_changed',
                    message=f"Payment updated: {', '.join(fields.keys())}" + (f" - {reason}" if reason else ""),
                    metadata={'fields_updated': list(fields.keys()), 'reason': reason},
                    changed_by=changed_by
                )
            
            # Audit logging
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='payments',
                    message=f"Payment updated: {payment_id}, fields: {list(fields.keys())}, reason: {reason}",
                    func_name='update_payment',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_payment
        except Exception as e:
            logger.error(f"Error updating payment {payment_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def delete_payment(payment_id: str, changed_by=None, reason: str = None, hard_delete: bool = False) -> bool:
        """
        Delete a payment (soft delete by default, hard delete if hard_delete=True).
        
        Args:
            payment_id: UUID of the payment
            changed_by: User deleting the payment
            reason: Reason for deletion
            hard_delete: If True, permanently delete; otherwise soft delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for deletion")
                return False
            
            if hard_delete:
                PaymentRepository.delete_payment(payment)
            else:
                PaymentRepository.soft_delete_payment(payment, deleted_by=changed_by)
            
            # Audit logging
            try:
                delete_type = "hard deleted" if hard_delete else "soft deleted"
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='payments',
                    message=f"Payment {delete_type}: {payment_id}, reason: {reason}",
                    func_name='delete_payment',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except ObjectDoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting payment {payment_id}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def restore_payment(payment_id: str, restored_by=None) -> Optional[Payment]:
        """
        Restore a soft-deleted payment.
        
        Args:
            payment_id: UUID of the payment
            restored_by: User restoring the payment
            
        Returns:
            Restored Payment instance or None on error
        """
        try:
            # Get payment including deleted ones
            payment = PaymentSelector.get_deleted_by_id(payment_id)
            
            restored_payment = PaymentRepository.restore_payment(payment, restored_by=restored_by)
            
            # Create history entry
            PaymentHistoryService.create_history_entry(
                payment=restored_payment,
                event_type='status_changed',
                message=f"Payment restored",
                changed_by=restored_by
            )
            
            # Audit logging
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='payments',
                    message=f"Payment restored: {payment_id}",
                    func_name='restore_payment',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return restored_payment
        except ObjectDoesNotExist:
            logger.error(f"Payment {payment_id} not found or not deleted")
            return None
        except Exception as e:
            logger.error(f"Error restoring payment {payment_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def get_by_filters(
        case_id: str = None,
        status: str = None,
        payment_provider: str = None,
        currency: str = None,
        date_from=None,
        date_to=None
    ) -> QuerySet:
        """
        Get payments with filters for admin functionality.
        
        Args:
            case_id: Filter by case ID
            status: Filter by status
            payment_provider: Filter by payment provider
            currency: Filter by currency
            date_from: Filter by created date (from)
            date_to: Filter by created date (to)
            
        Returns:
            QuerySet of filtered payments
        """
        return PaymentSelector.get_by_filters(
            case_id=case_id,
            status=status,
            payment_provider=payment_provider,
            currency=currency,
            date_from=date_from,
            date_to=date_to
        )

    @staticmethod
    def get_statistics() -> dict:
        """
        Get payment statistics for admin analytics.
        
        Returns:
            Dictionary with payment statistics
        """
        return PaymentSelector.get_statistics()
    
    @staticmethod
    def initiate_payment(
        payment_id: str,
        return_url: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate payment with payment gateway.
        
        Args:
            payment_id: UUID of the payment
            return_url: URL to redirect after payment completion
            callback_url: URL for webhook callbacks
            
        Returns:
            Dict with payment_url, transaction_id, etc. or None on error
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for initiation")
                return None
            
            if not payment.payment_provider:
                logger.error(f"Payment {payment_id} has no payment provider")
                return None
            
            # Initialize payment with gateway
            result = PaymentGatewayService.initialize_payment(
                payment=payment,
                return_url=return_url,
                callback_url=callback_url
            )
            
            # Create history entry for gateway initiation
            PaymentHistoryService.create_history_entry(
                payment=payment,
                event_type='gateway_initiated',
                message=f"Payment initiated with {payment.payment_provider} gateway",
                metadata={'gateway_response': result},
            )
            
            # Update payment with transaction ID
            if result.get('transaction_id'):
                PaymentService.update_payment(
                    payment_id=payment_id,
                    provider_transaction_id=result.get('transaction_id'),
                    status='processing',
                    changed_by=None,
                    reason="Payment initiated with gateway"
                )
            
            return result
            
        except PaymentGatewayError as e:
            logger.error(f"Payment gateway error initiating payment {payment_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error initiating payment {payment_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def verify_payment_status(payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Verify payment status with payment gateway.
        
        Args:
            payment_id: UUID of the payment
            
        Returns:
            Dict with payment status, amount, etc. or None on error
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for verification")
                return None
            
            if not payment.payment_provider or not payment.provider_transaction_id:
                logger.error(f"Payment {payment_id} missing provider or transaction ID")
                return None
            
            # Verify payment with gateway
            result = PaymentGatewayService.verify_payment(payment)
            
            # Create history entry for verification
            PaymentHistoryService.create_history_entry(
                payment=payment,
                event_type='gateway_verified',
                message=f"Payment verified with {payment.payment_provider} gateway",
                metadata={'verification_result': result},
            )
            
            # Update payment status if changed
            if result.get('status') and payment.status != result.get('status'):
                PaymentService.update_payment(
                    payment_id=payment_id,
                    status=result.get('status'),
                    changed_by=None,
                    reason="Payment status verified with gateway"
                )
            
            return result
            
        except PaymentGatewayError as e:
            logger.error(f"Payment gateway error verifying payment {payment_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error verifying payment {payment_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def process_refund(
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a refund for a payment.
        
        Args:
            payment_id: UUID of the payment
            amount: Optional refund amount (partial refund if specified)
            reason: Optional refund reason
            
        Returns:
            Dict with refund_id, amount, status or None on error
        """
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for refund")
                return None
            
            # Process refund with gateway
            result = PaymentGatewayService.refund_payment(
                payment=payment,
                amount=amount,
                reason=reason
            )
            
            # Update payment status to refunded
            if result.get('success'):
                PaymentService.update_payment(
                    payment_id=payment_id,
                    status='refunded',
                    changed_by=None,
                    reason=f"Refund processed: {reason or 'No reason provided'}"
                )
            
            return result
            
        except PaymentGatewayError as e:
            logger.error(f"Payment gateway error processing refund {payment_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error processing refund {payment_id}: {e}", exc_info=True)
            return None