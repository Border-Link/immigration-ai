import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from human_reviews.selectors.review_status_history_selector import ReviewStatusHistorySelector
from human_reviews.serializers.review_status_history.read import ReviewStatusHistorySerializer, ReviewStatusHistoryListSerializer

logger = logging.getLogger('django')


class ReviewStatusHistoryListAPI(AuthAPI):
    """
    Get status history for a review.
    
    Endpoint: GET /api/v1/human-reviews/reviews/<review_id>/status-history/
    Auth: Required
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, review_id):
        try:
            from human_reviews.selectors.review_selector import ReviewSelector
            review = ReviewSelector.get_by_id(review_id)
            if not review:
                return self.api_response(
                    message=f"Review with ID '{review_id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            history = ReviewStatusHistorySelector.get_by_review(review)
            
            return self.api_response(
                message="Review status history retrieved successfully.",
                data=ReviewStatusHistoryListSerializer(history, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving review status history: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving review status history.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewStatusHistoryDetailAPI(AuthAPI):
    """
    Get detailed status history entry.
    
    Endpoint: GET /api/v1/human-reviews/status-history/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            history = ReviewStatusHistorySelector.get_by_id(id)
            if not history:
                return self.api_response(
                    message=f"Status history entry with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Status history entry retrieved successfully.",
                data=ReviewStatusHistorySerializer(history).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving status history entry {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving status history entry.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
