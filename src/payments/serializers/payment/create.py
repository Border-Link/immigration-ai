from rest_framework import serializers
from decimal import Decimal
from django.core.exceptions import ValidationError
from immigration_cases.selectors.case_selector import CaseSelector
from payments.models.payment import Payment

# Currency-specific amount limits
CURRENCY_LIMITS = {
    'USD': {'min': Decimal('0.01'), 'max': Decimal('10000.00')},
    'GBP': {'min': Decimal('0.01'), 'max': Decimal('8000.00')},
    'EUR': {'min': Decimal('0.01'), 'max': Decimal('9000.00')},
    'CAD': {'min': Decimal('0.01'), 'max': Decimal('13000.00')},
    'AUD': {'min': Decimal('0.01'), 'max': Decimal('14000.00')},
    'JPY': {'min': Decimal('1.00'), 'max': Decimal('1000000.00')},
    'CHF': {'min': Decimal('0.01'), 'max': Decimal('9000.00')},
    'NZD': {'min': Decimal('0.01'), 'max': Decimal('15000.00')},
    'SGD': {'min': Decimal('0.01'), 'max': Decimal('13000.00')},
    'HKD': {'min': Decimal('0.01'), 'max': Decimal('78000.00')},
    'NGN': {'min': Decimal('0.01'), 'max': Decimal('4000000.00')},
    'AED': {'min': Decimal('0.01'), 'max': Decimal('37000.00')},
    'ZAR': {'min': Decimal('0.01'), 'max': Decimal('150000.00')},
    'INR': {'min': Decimal('0.01'), 'max': Decimal('800000.00')},
}


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating a payment."""
    
    case_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(required=True, max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.ChoiceField(
        choices=Payment.SUPPORTED_CURRENCIES,
        required=False,
        default=Payment.DEFAULT_CURRENCY,
        help_text="Currency code (ISO 4217). Defaults to USD."
    )
    status = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES,
        required=False,
        default='pending'
    )
    payment_provider = serializers.ChoiceField(
        choices=Payment.PAYMENT_PROVIDER_CHOICES,
        required=True,
        help_text="Payment gateway provider (stripe, paypal, or adyen)"
    )
    provider_transaction_id = serializers.CharField(required=False, max_length=255, allow_null=True, allow_blank=True)

    def validate_case_id(self, value):
        """Validate case exists."""
        try:
            case = CaseSelector.get_by_id(value)
            if not case:
                raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        return value
    
    def validate(self, attrs):
        """Validate payment data including currency-specific amount limits."""
        amount = attrs.get('amount')
        currency = attrs.get('currency', Payment.DEFAULT_CURRENCY)
        
        if amount:
            limits = CURRENCY_LIMITS.get(currency, CURRENCY_LIMITS['USD'])
            if amount < limits['min']:
                raise serializers.ValidationError({
                    'amount': f"Amount must be at least {limits['min']} {currency}"
                })
            if amount > limits['max']:
                raise serializers.ValidationError({
                    'amount': f"Amount cannot exceed {limits['max']} {currency}"
                })
        
        return attrs

