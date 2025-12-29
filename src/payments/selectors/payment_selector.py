from payments.models.payment import Payment
from immigration_cases.models.case import Case


class PaymentSelector:
    """Selector for Payment read operations."""

    @staticmethod
    def get_all():
        """Get all payments."""
        return Payment.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).all().order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get payments by case."""
        return Payment.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(case=case).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str):
        """Get payments by status."""
        return Payment.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(status=status).order_by('-created_at')

    @staticmethod
    def get_by_provider_transaction_id(transaction_id: str):
        """Get payment by provider transaction ID."""
        return Payment.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(provider_transaction_id=transaction_id).first()

    @staticmethod
    def get_by_id(payment_id):
        """Get payment by ID."""
        return Payment.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).get(id=payment_id)

