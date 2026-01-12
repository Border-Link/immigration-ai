from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.review_permission import ReviewPermission
from human_reviews.services.review_service import ReviewService
from human_reviews.serializers.review.create import ReviewCreateSerializer
from human_reviews.serializers.review.read import ReviewSerializer


class ReviewCreateAPI(AuthAPI):
    """Create a new review. Authenticated users can create reviews."""
    permission_classes = [ReviewPermission]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.create_review(
            case_id=serializer.validated_data.get('case_id'),
            reviewer_id=serializer.validated_data.get('reviewer_id'),
            auto_assign=serializer.validated_data.get('auto_assign', True),
            assignment_strategy=serializer.validated_data.get('assignment_strategy', 'round_robin')
        )

        if not review:
            return self.api_response(
                message="Error creating review.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Review created successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_201_CREATED
        )

