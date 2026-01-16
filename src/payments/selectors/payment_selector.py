"""
Payment Selector

Read operations for Payment model.
All database read operations must live here - no state mutations.
"""
from django.db.models import QuerySet, Count, Sum, Avg, Q
from django.utils import timezone
from payments.models.payment import Payment
from immigration_cases.models.case import Case


class PaymentSelector:
    """Selector for Payment read operations."""

    @staticmethod
    def get_all() -> QuerySet:
        """Get all non-deleted payments."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_user(user) -> QuerySet:
        """Get non-deleted payments by user."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(user=user, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_case(case: Case) -> QuerySet:
        """Get non-deleted payments by case."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(case=case, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_status(status: str) -> QuerySet:
        """Get non-deleted payments by status."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(status=status, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_provider_transaction_id(transaction_id: str) -> Payment:
        """Get non-deleted payment by provider transaction ID."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(provider_transaction_id=transaction_id, is_deleted=False).first()

    @staticmethod
    def get_by_id(payment_id) -> Payment:
        """Get non-deleted payment by ID."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(is_deleted=False).get(id=payment_id)

    @staticmethod
    def get_completed_case_fee_by_id(payment_id) -> Payment:
        """
        Get a completed, non-deleted case_fee payment by id.

        Returns None if not found.
        """
        return Payment.objects.select_related(
            "user",
            "user__profile",
            "case",
            "case__user",
            "case__user__profile",
        ).filter(
            id=payment_id,
            status="completed",
            is_deleted=False,
            purpose="case_fee",
        ).first()

    @staticmethod
    def get_deleted_by_id(payment_id) -> Payment:
        """Get deleted payment by ID (for restore operations)."""
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case',
            'case__user',
            'case__user__profile'
        ).filter(is_deleted=True).get(id=payment_id)

    @staticmethod
    def get_unassigned_completed_by_user(user) -> QuerySet:
        """
        Get completed payments for a user that are not yet attached to a case.

        This supports the "pay before case creation" flow:
        - Create payment (user)
        - Complete payment
        - Create case -> attach payment to case
        """
        return Payment.objects.select_related(
            'user',
            'user__profile',
            'case'
        ).filter(
            user=user,
            case__isnull=True,
            status='completed',
            purpose='case_fee',
            is_deleted=False
        ).order_by('-created_at')

    @staticmethod
    def get_none() -> QuerySet:
        """Get empty queryset."""
        return Payment.objects.none()

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
            currency: Filter by currency (ignored - all payments are USD)
            date_from: Filter by created date (from)
            date_to: Filter by created date (to)
            
        Returns:
            QuerySet of filtered payments
        """
        queryset = Payment.objects.select_related(
            'case',
            'case__user',
            'case__user__profile'
        ).filter(is_deleted=False)
        
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if payment_provider:
            queryset = queryset.filter(payment_provider=payment_provider)
        
        # Currency filter - implement currency filtering
        if currency:
            queryset = queryset.filter(currency=currency)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_statistics() -> dict:
        """
        Get payment statistics for admin analytics.
        
        Returns:
            Dictionary with payment statistics
        """
        # Filter out deleted payments for all statistics
        base_queryset = Payment.objects.filter(is_deleted=False)
        
        total_payments = base_queryset.count()
        
        # Status breakdown
        status_breakdown = base_queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Provider breakdown
        provider_breakdown = base_queryset.values('payment_provider').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).exclude(payment_provider__isnull=True)
        
        # Currency breakdown
        currency_breakdown = base_queryset.values('currency').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Total revenue (completed payments only)
        total_revenue = base_queryset.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Average payment amount
        avg_payment = base_queryset.aggregate(
            avg=Avg('amount')
        )['avg'] or 0
        
        # Recent payments (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_payments = base_queryset.filter(created_at__gte=thirty_days_ago).count()
        
        # Pending payments
        pending_payments = base_queryset.filter(status='pending').count()
        
        # Failed payments
        failed_payments = base_queryset.filter(status='failed').count()
        
        return {
            'total_payments': total_payments,
            'total_revenue': float(total_revenue),
            'average_payment': float(avg_payment),
            'recent_payments_30_days': recent_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'status_breakdown': list(status_breakdown),
            'provider_breakdown': list(provider_breakdown),
            'currency_breakdown': list(currency_breakdown),
        }