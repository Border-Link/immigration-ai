from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_reviewer import IsReviewer
from human_reviews.services.decision_override_service import DecisionOverrideService
from human_reviews.serializers.decision_override.create import DecisionOverrideCreateSerializer
from human_reviews.serializers.decision_override.read import DecisionOverrideSerializer


class DecisionOverrideCreateAPI(AuthAPI):
    """Create a new decision override. Only reviewers can create overrides."""
    permission_classes = [IsReviewer]

    def post(self, request):
        serializer = DecisionOverrideCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use authenticated user as reviewer if not provided
        reviewer_id = serializer.validated_data.get('reviewer_id')
        if not reviewer_id:
            reviewer_id = request.user.id

        override = DecisionOverrideService.create_decision_override(
            case_id=serializer.validated_data.get('case_id'),
            original_result_id=serializer.validated_data.get('original_result_id'),
            overridden_outcome=serializer.validated_data.get('overridden_outcome'),
            reason=serializer.validated_data.get('reason'),
            reviewer_id=reviewer_id,
            review_id=serializer.validated_data.get('review_id')
        )

        if not override:
            return self.api_response(
                message="Error creating decision override.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Decision override created successfully.",
            data=DecisionOverrideSerializer(override).data,
            status_code=status.HTTP_201_CREATED
        )

