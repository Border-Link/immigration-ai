"""
Payment History Serializers

Serializers for payment history operations.
"""
from rest_framework import serializers
from payments.models.payment_history import PaymentHistory


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history entries."""
    
    changed_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id',
            'event_type',
            'previous_status',
            'new_status',
            'message',
            'metadata',
            'changed_by_email',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_changed_by_email(self, obj):
        """Get email of user who made the change."""
        return obj.changed_by.email if obj.changed_by else None
