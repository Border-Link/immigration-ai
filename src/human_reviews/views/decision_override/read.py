from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_reviewer import IsReviewer
from human_reviews.services.decision_override_service import DecisionOverrideService
from human_reviews.serializers.decision_override.read import DecisionOverrideSerializer, DecisionOverrideListSerializer


class DecisionOverrideListAPI(AuthAPI):
    """Get list of decision overrides. Supports filtering by case_id, original_result_id, reviewer_id. Only reviewers can access."""
    permission_classes = [IsReviewer]

    def get(self, request):
        case_id = request.query_params.get('case_id', None)
        original_result_id = request.query_params.get('original_result_id', None)
        reviewer_id = request.query_params.get('reviewer_id', None)

        if case_id:
            overrides = DecisionOverrideService.get_by_case(case_id)
        elif original_result_id:
            overrides = DecisionOverrideService.get_by_original_result(original_result_id)
        elif reviewer_id:
            overrides = DecisionOverrideService.get_by_reviewer(reviewer_id)
        else:
            overrides = DecisionOverrideService.get_all()

        return self.api_response(
            message="Decision overrides retrieved successfully.",
            data=DecisionOverrideListSerializer(overrides, many=True).data,
            status_code=status.HTTP_200_OK
        )


class DecisionOverrideDetailAPI(AuthAPI):
    """Get decision override by ID. Only reviewers can access."""
    permission_classes = [IsReviewer]

    def get(self, request, id):
        override = DecisionOverrideService.get_by_id(id)
        if not override:
            return self.api_response(
                message=f"Decision override with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Decision override retrieved successfully.",
            data=DecisionOverrideSerializer(override).data,
            status_code=status.HTTP_200_OK
        )


class DecisionOverrideLatestAPI(AuthAPI):
    """Get latest override for an eligibility result. Only reviewers can access."""
    permission_classes = [IsReviewer]

    def get(self, request, original_result_id):
        override = DecisionOverrideService.get_latest_by_original_result(original_result_id)
        if not override:
            return self.api_response(
                message=f"No override found for eligibility result '{original_result_id}'.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Latest decision override retrieved successfully.",
            data=DecisionOverrideSerializer(override).data,
            status_code=status.HTTP_200_OK
        )

