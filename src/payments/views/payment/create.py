from rest_framework import status
from main_system.base.auth_api import AuthAPI
from payments.models.payment import Payment
from payments.services.payment_service import PaymentService
from payments.serializers.payment.create import PaymentCreateSerializer
from payments.serializers.payment.read import PaymentSerializer


class PaymentCreateAPI(AuthAPI):
    """Create a new payment. Authenticated users can create payments."""

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.create_payment(
            case_id=str(serializer.validated_data.get('case_id')),
            amount=serializer.validated_data.get('amount'),
            currency=serializer.validated_data.get('currency', Payment.DEFAULT_CURRENCY),
            status=serializer.validated_data.get('status', 'pending'),
            payment_provider=serializer.validated_data.get('payment_provider'),
            provider_transaction_id=serializer.validated_data.get('provider_transaction_id'),
            changed_by=request.user
        )

        if not payment:
            return self.api_response(
                message="Error creating payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Payment created successfully.",
            data=PaymentSerializer(payment).data,
            status_code=status.HTTP_201_CREATED
        )

