"""
Admin Serializers for Payment Management

Serializers for admin payment management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from payments.models.payment import Payment


class PaymentAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    case_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES,
        required=False,
        allow_null=True
    )
    payment_provider = serializers.ChoiceField(
        choices=Payment.PAYMENT_PROVIDER_CHOICES,
        required=False,
        allow_null=True
    )
    # Currency filtering removed - all payments are in USD


class PaymentAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating a payment in admin view."""
    status = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES,
        required=False
    )
    payment_provider = serializers.ChoiceField(
        choices=Payment.PAYMENT_PROVIDER_CHOICES,
        required=False,
        allow_null=True
    )
    provider_transaction_id = serializers.CharField(
        required=False,
        max_length=255,
        allow_null=True,
        allow_blank=True
    )
    version = serializers.IntegerField(
        required=False,
        help_text="Version number for optimistic locking"
    )


class BulkPaymentOperationSerializer(serializers.Serializer):
    """Serializer for bulk payment operations."""
    payment_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'update_status',
    ])
    status = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES,
        required=False,
        help_text="Required for update_status operation"
    )

    def validate(self, attrs):
        """Validate that status is provided for update_status operation."""
        operation = attrs.get('operation')
        status = attrs.get('status')
        
        if operation == 'update_status' and not status:
            raise serializers.ValidationError({
                'status': 'Status is required for update_status operation.'
            })
        
        return attrs
