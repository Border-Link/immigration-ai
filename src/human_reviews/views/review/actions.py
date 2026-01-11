from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from human_reviews.services.review_service import ReviewService
from human_reviews.serializers.review.read import ReviewSerializer
from human_reviews.serializers.review.actions import (
    ReviewReassignSerializer,
    ReviewEscalateSerializer,
    ReviewApproveSerializer,
    ReviewRejectSerializer,
    ReviewRequestChangesSerializer,
)


class ReviewReassignAPI(AuthAPI):
    """
    Reassign a review to a different reviewer.
    
    Endpoint: POST /api/v1/human-reviews/reviews/<id>/reassign/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = ReviewReassignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = ReviewService.reassign_reviewer(
            review_id=id,
            new_reviewer_id=str(serializer.validated_data['new_reviewer_id']),
            changed_by_id=str(request.user.id),
            reason=serializer.validated_data.get('reason')
        )
        
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found or reassignment failed.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Review reassigned successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewEscalateAPI(AuthAPI):
    """
    Escalate a review for urgent attention.
    
    Endpoint: POST /api/v1/human-reviews/reviews/<id>/escalate/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = ReviewEscalateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = ReviewService.escalate_review(
            review_id=id,
            escalated_by_id=str(request.user.id),
            reason=serializer.validated_data.get('reason'),
            priority=serializer.validated_data.get('priority', 'high')
        )
        
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found or escalation failed.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Review escalated successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewApproveAPI(AuthAPI):
    """
    Approve a review.
    
    Endpoint: POST /api/v1/human-reviews/reviews/<id>/approve/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = ReviewApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = ReviewService.approve_review(
            review_id=id,
            approved_by_id=str(request.user.id),
            reason=serializer.validated_data.get('reason')
        )
        
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found or approval failed.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Review approved successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewRejectAPI(AuthAPI):
    """
    Reject a review.
    
    Endpoint: POST /api/v1/human-reviews/reviews/<id>/reject/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = ReviewRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = ReviewService.reject_review(
            review_id=id,
            rejected_by_id=str(request.user.id),
            reason=serializer.validated_data.get('reason')
        )
        
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found or rejection failed.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Review rejected successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )


class ReviewRequestChangesAPI(AuthAPI):
    """
    Request changes on a review.
    
    Endpoint: POST /api/v1/human-reviews/reviews/<id>/request-changes/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request, id):
        serializer = ReviewRequestChangesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = ReviewService.request_changes(
            review_id=id,
            requested_by_id=str(request.user.id),
            reason=serializer.validated_data.get('reason')
        )
        
        if not review:
            return self.api_response(
                message=f"Review with ID '{id}' not found or request changes failed.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return self.api_response(
            message="Changes requested successfully.",
            data=ReviewSerializer(review).data,
            status_code=status.HTTP_200_OK
        )
