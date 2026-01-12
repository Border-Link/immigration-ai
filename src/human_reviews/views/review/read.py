from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.review_permission import ReviewPermission
from human_reviews.services.review_service import ReviewService
from human_reviews.serializers.review.read import ReviewSerializer, ReviewListSerializer


class ReviewListAPI(AuthAPI):
    """Get list of reviews. Supports filtering by status, case_id, reviewer_id. Only reviewers can access."""
    permission_classes = [ReviewPermission]

    def get(self, request):
        status_filter = request.query_params.get('status', None)
        case_id = request.query_params.get('case_id', None)
        reviewer_id = request.query_params.get('reviewer_id', None)

        if case_id:
            reviews = ReviewService.get_by_case(case_id)
        elif reviewer_id:
            reviews = ReviewService.get_by_reviewer(reviewer_id)
        elif status_filter:
            reviews = ReviewService.get_by_status(status_filter)
        else:
            reviews = ReviewService.get_all()

        return self.api_response(
            message="Reviews retrieved successfully.",
            data=ReviewListSerializer(reviews, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ReviewDetailAPI(AuthAPI):
    """Get review by ID. Only reviewers can access."""
    permission_classes = [ReviewPermission]

    def get(self, request, id):
        review = ReviewService.get_by_id(id)
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review retrieved successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewPendingAPI(AuthAPI):
    """Get all pending reviews (not assigned). Only reviewers/admins can access."""
    permission_classes = [ReviewPermission]

    def get(self, request):
        reviews = ReviewService.get_pending()

        return self.api_response(
            message="Pending reviews retrieved successfully.",
            data=ReviewListSerializer(reviews, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ReviewByReviewerAPI(AuthAPI):
    """Get pending/in_progress reviews for the authenticated reviewer. Only reviewers can access."""
    permission_classes = [ReviewPermission]

    def get(self, request):
        reviewer_id = request.user.id
        reviews = ReviewService.get_pending_by_reviewer(reviewer_id)

        return self.api_response(
            message="Reviews retrieved successfully.",
            data=ReviewListSerializer(reviews, many=True).data,
            status_code=status.HTTP_200_OK
        )

