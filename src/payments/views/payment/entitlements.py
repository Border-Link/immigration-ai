from rest_framework import status

from main_system.base.auth_api import AuthAPI
from main_system.permissions.payment_permission import PaymentPermission
from immigration_cases.selectors.case_selector import CaseSelector
from payments.helpers.payment_validator import PaymentValidator


class CaseEntitlementsAPI(AuthAPI):
    """
    Return computed entitlements for a case.

    Endpoint: GET /api/v1/payments/cases/<case_id>/entitlements/

    Intended for UI clients to determine which features are enabled for a case.
    """

    permission_classes = [PaymentPermission]

    def get(self, request, case_id):
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

        has_case_fee, _payment = PaymentValidator.has_completed_payment_for_case(case, use_cache=True)
        plan = PaymentValidator.get_case_fee_plan_for_case(case) if has_case_fee else None

        ai_calls_ok, _ = PaymentValidator.validate_case_has_ai_calls_entitlement(case, operation_name="AI calls")
        human_review_ok, _ = PaymentValidator.validate_case_has_human_review_entitlement(case, operation_name="human review")

        return self.api_response(
            message="Entitlements fetched successfully.",
            data={
                "has_case_fee_payment": bool(has_case_fee),
                "plan": plan,
                "entitlements": {
                    "case_creation": bool(has_case_fee),
                    "ai_decisioning": bool(has_case_fee),
                    "document_processing": bool(has_case_fee),
                    "ai_calls": bool(has_case_fee and ai_calls_ok),
                    "human_review": bool(has_case_fee and human_review_ok),
                },
            },
            status_code=status.HTTP_200_OK,
        )

