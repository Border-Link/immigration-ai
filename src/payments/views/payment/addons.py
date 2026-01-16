from decimal import Decimal

from rest_framework import status

from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from immigration_cases.selectors.case_selector import CaseSelector
from payments.helpers.payment_validator import PaymentValidator
from payments.helpers.plan_pricing import PlanPricing
from payments.models.payment import Payment
from payments.serializers.payment.read import PaymentSerializer
from payments.serializers.payment.reviewer_addon_purchase import ReviewerAddonPurchaseSerializer
from payments.services.payment_service import PaymentService


class CaseReviewerAddonPurchaseAPI(AuthAPI):
    """
    Purchase the Immigration Reviewer add-on for a case.

    Endpoint: POST /api/v1/payments/cases/<case_id>/reviewer-addon/

    NOTE: amount is derived server-side from settings.
    """

    permission_classes = [PaymentPermission]

    def post(self, request, case_id):
        serializer = ReviewerAddonPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = CaseSelector.get_by_id(str(case_id))
        if not case:
            return self.api_response(
                message="Case not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Enforce case ownership for add-on purchase.
        if str(case.user_id) != str(request.user.id):
            return self.api_response(
                message="Forbidden.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Must have a completed base case payment first.
        ok, err = PaymentValidator.validate_case_has_payment(case, operation_name="reviewer add-on purchase")
        if not ok:
            return self.api_response(
                message=err,
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # If already entitled (plan includes or add-on already purchased), don't allow purchasing again.
        entitled, _ = PaymentValidator.validate_case_has_human_review_entitlement(case, operation_name="human review")
        if entitled:
            return self.api_response(
                message="Case already has human review entitlement; reviewer add-on is not required.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        currency = serializer.validated_data.get("currency", Payment.DEFAULT_CURRENCY)
        amount = PlanPricing.get_reviewer_addon_amount(currency=currency)
        if amount is None:
            return self.api_response(
                message="Reviewer add-on pricing not configured for this currency.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        payment_provider = serializer.validated_data["payment_provider"]

        payment = PaymentService.create_payment(
            case_id=str(case.id),
            amount=amount,
            currency=currency,
            status="pending",
            payment_provider=payment_provider,
            provider_transaction_id=None,
            purpose="reviewer_addon",
            plan=None,
            changed_by=request.user,
        )

        if not payment:
            return self.api_response(
                message="Error creating reviewer add-on payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return self.api_response(
            message="Reviewer add-on payment created successfully.",
            data=PaymentSerializer(payment).data,
            status_code=status.HTTP_201_CREATED,
        )


class CaseAiCallsAddonPurchaseAPI(AuthAPI):
    """
    Purchase the AI Calls add-on for a case (for Basic plan users).

    Endpoint: POST /api/v1/payments/cases/<case_id>/ai-calls-addon/

    NOTE: amount is derived server-side from pricing config.
    """

    permission_classes = [PaymentPermission]

    def post(self, request, case_id):
        serializer = ReviewerAddonPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = CaseSelector.get_by_id(str(case_id))
        if not case:
            return self.api_response(
                message="Case not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if str(case.user_id) != str(request.user.id):
            return self.api_response(
                message="Forbidden.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        ok, err = PaymentValidator.validate_case_has_payment(case, operation_name="ai calls add-on purchase")
        if not ok:
            return self.api_response(message=err, data=None, status_code=status.HTTP_400_BAD_REQUEST)

        # If already entitled (plan includes or add-on already purchased), don't allow purchasing again.
        entitled, _ = PaymentValidator.validate_case_has_ai_calls_entitlement(case, operation_name="AI calls")
        if entitled:
            return self.api_response(
                message="Case already has AI calls entitlement; add-on is not required.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        currency = serializer.validated_data.get("currency", Payment.DEFAULT_CURRENCY)
        amount = PlanPricing.get_ai_calls_addon_amount(currency=currency)
        if amount is None:
            return self.api_response(
                message="AI calls add-on pricing not configured for this currency.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payment_provider = serializer.validated_data["payment_provider"]
        payment = PaymentService.create_payment(
            case_id=str(case.id),
            amount=amount,
            currency=currency,
            status="pending",
            payment_provider=payment_provider,
            provider_transaction_id=None,
            purpose="ai_calls_addon",
            plan=None,
            changed_by=request.user,
        )

        if not payment:
            return self.api_response(
                message="Error creating AI calls add-on payment.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return self.api_response(
            message="AI calls add-on payment created successfully.",
            data=PaymentSerializer(payment).data,
            status_code=status.HTTP_201_CREATED,
        )

