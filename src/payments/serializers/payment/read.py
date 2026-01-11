from rest_framework import serializers
from payments.models.payment import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    case_user_email = serializers.EmailField(source='case.user.email', read_only=True)
    version = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'case_id',
            'case_user_email',
            'amount',
            'currency',
            'status',
            'payment_provider',
            'provider_transaction_id',
            'version',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class PaymentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing payments."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'case_id',
            'amount',
            'currency',
            'status',
            'payment_provider',
            'created_at',
        ]
        read_only_fields = '__all__'

