from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.review_permission import ReviewPermission
from human_reviews.services.review_service import ReviewService
from human_reviews.serializers.review.read import ReviewSerializer
from human_reviews.serializers.review.update_delete import ReviewUpdateSerializer, ReviewAssignSerializer


class ReviewUpdateAPI(AuthAPI):
    """Update a review. Only reviewers can access."""
    permission_classes = [ReviewPermission]

    def patch(self, request, id):
        serializer = ReviewUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.update_review(id, **serializer.validated_data)
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review updated successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewAssignAPI(AuthAPI):
    """Assign a reviewer to a review. Only reviewers/admins can access."""
    permission_classes = [ReviewPermission]

    def post(self, request, id):
        serializer = ReviewAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.assign_reviewer(
            review_id=id,
            reviewer_id=serializer.validated_data.get('reviewer_id'),
            assignment_strategy=serializer.validated_data.get('assignment_strategy', 'round_robin')
        )
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found or no available reviewers.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Reviewer assigned successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewCompleteAPI(AuthAPI):
    """Complete a review. Only reviewers can access."""
    permission_classes = [ReviewPermission]

    def post(self, request, id):
        review = ReviewService.complete_review(id)
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review completed successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewCancelAPI(AuthAPI):
    """Cancel a review. Only reviewers/admins can access."""
    permission_classes = [ReviewPermission]

    def post(self, request, id):
        review = ReviewService.cancel_review(id)
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review cancelled successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewDeleteAPI(AuthAPI):
    """Delete a review. Only reviewers/admins can access."""
    permission_classes = [ReviewPermission]

    def delete(self, request, id):
        success = ReviewService.delete_review(id)
        if not success:
            return self.api_response(
                message=f"Review with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

