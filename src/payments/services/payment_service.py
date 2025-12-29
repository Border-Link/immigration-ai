import logging
from typing import Optional
from decimal import Decimal
from payments.models.payment import Payment
from payments.repositories.payment_repository import PaymentRepository
from payments.selectors.payment_selector import PaymentSelector
from immigration_cases.selectors.case_selector import CaseSelector

logger = logging.getLogger('django')


class PaymentService:
    """Service for Payment business logic."""

    @staticmethod
    def create_payment(case_id: str, amount: Decimal, currency: str = 'GBP', status: str = 'pending',
                      payment_provider: str = None, provider_transaction_id: str = None) -> Optional[Payment]:
        """Create a new payment."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return PaymentRepository.create_payment(
                case=case,
                amount=amount,
                currency=currency,
                status=status,
                payment_provider=payment_provider,
                provider_transaction_id=provider_transaction_id
            )
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all payments."""
        try:
            return PaymentSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all payments: {e}")
            return Payment.objects.none()

    @staticmethod
    def get_by_case(case_id: str):
        """Get payments by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return PaymentSelector.get_by_case(case)
        except Exception as e:
            logger.error(f"Error fetching payments for case {case_id}: {e}")
            return Payment.objects.none()

    @staticmethod
    def get_by_status(status: str):
        """Get payments by status."""
        try:
            return PaymentSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching payments by status {status}: {e}")
            return Payment.objects.none()

    @staticmethod
    def get_by_provider_transaction_id(transaction_id: str) -> Optional[Payment]:
        """Get payment by provider transaction ID."""
        try:
            return PaymentSelector.get_by_provider_transaction_id(transaction_id)
        except Exception as e:
            logger.error(f"Error fetching payment by transaction ID {transaction_id}: {e}")
            return None

    @staticmethod
    def get_by_id(payment_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        try:
            return PaymentSelector.get_by_id(payment_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching payment {payment_id}: {e}")
            return None

    @staticmethod
    def update_payment(payment_id: str, **fields) -> Optional[Payment]:
        """Update payment fields."""
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            return PaymentRepository.update_payment(payment, **fields)
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating payment {payment_id}: {e}")
            return None

    @staticmethod
    def delete_payment(payment_id: str) -> bool:
        """Delete a payment."""
        try:
            payment = PaymentSelector.get_by_id(payment_id)
            PaymentRepository.delete_payment(payment)
            return True
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting payment {payment_id}: {e}")
            return False

