from decimal import Decimal

from rest_framework import status

from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from payments.helpers.plan_pricing import PlanPricing
from payments.models.payment import Payment
from payments.serializers.payment.plan_purchase import PlanPurchaseSerializer
from payments.serializers.payment.read import PaymentSerializer
from payments.services.payment_service import PaymentService


class PlanCaseFeePurchaseAPI(AuthAPI):
    """
    Purchase a plan as a pre-case (user) payment.

    Endpoint: POST /api/v1/payments/plans/case-fee/

    Body:
      - plan: basic|special|big
      - payment_provider: stripe|paypal|adyen|bank_transfer
      - currency (optional)

    NOTE: amount is derived server-side from settings.
    """

    permission_classes = [PaymentPermission]

    def post(self, request):
        serializer = PlanPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data["plan"]
        currency = serializer.validated_data.get("currency", Payment.DEFAULT_CURRENCY)
        payment_provider = serializer.validated_data["payment_provider"]

        amount = PlanPricing.get_case_fee_amount(plan=plan, currency=currency)
        if amount is None:
            return self.api_response(
                message="Plan pricing not configured for this currency.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payment = PaymentService.create_payment(
            user_id=str(request.user.id),
            amount=amount,
            currency=currency,
            status="pending",
            payment_provider=payment_provider,
            provider_transaction_id=None,
            purpose="case_fee",
            plan=plan,
            changed_by=request.user,
        )

        if not payment:
            return self.api_response(
                message="Error creating plan payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return self.api_response(
            message="Plan payment created successfully.",
            data=PaymentSerializer(payment).data,
            status_code=status.HTTP_201_CREATED,
        )

