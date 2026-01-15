from rest_framework import serializers
from payments.models.payment import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    case_id = serializers.SerializerMethodField()
    case_user_email = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    version = serializers.IntegerField(read_only=True)

    def get_case_id(self, obj):
        return str(obj.case_id) if obj.case_id else None

    def get_case_user_email(self, obj):
        if obj.case_id and obj.case and getattr(obj.case, "user", None):
            return obj.case.user.email
        return None
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'user_email',
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
    
    case_id = serializers.SerializerMethodField()

    def get_case_id(self, obj):
        return str(obj.case_id) if obj.case_id else None
    
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

