"""
Admin API Views for Review Management

Admin-only endpoints for managing reviews.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from human_reviews.services.review_service import ReviewService
from human_reviews.serializers.review.read import ReviewSerializer, ReviewListSerializer
from human_reviews.serializers.review.admin import (
    ReviewAdminListQuerySerializer,
    ReviewAdminUpdateSerializer,
    BulkReviewOperationSerializer,
)
from django.core.exceptions import ValidationError

logger = logging.getLogger('django')


class ReviewAdminListAPI(AuthAPI):
    """
    Admin: Get list of all reviews with advanced filtering.
    
    Endpoint: GET /api/v1/human-reviews/admin/reviews/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - reviewer_id: Filter by reviewer ID
        - status: Filter by status (pending, in_progress, completed, cancelled)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - assigned_date_from: Filter by assigned date (from)
        - assigned_date_to: Filter by assigned date (to)
        - completed_date_from: Filter by completed date (from)
        - completed_date_to: Filter by completed date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = ReviewAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Use service method with filters
        reviews = ReviewService.get_by_filters(
            case_id=str(validated_params.get('case_id')) if validated_params.get('case_id') else None,
            reviewer_id=str(validated_params.get('reviewer_id')) if validated_params.get('reviewer_id') else None,
            status=validated_params.get('status'),
            date_from=validated_params.get('date_from'),
            date_to=validated_params.get('date_to'),
            assigned_date_from=validated_params.get('assigned_date_from'),
            assigned_date_to=validated_params.get('assigned_date_to'),
            completed_date_from=validated_params.get('completed_date_from'),
            completed_date_to=validated_params.get('completed_date_to')
        )
        
        return self.api_response(
            message="Reviews retrieved successfully.",
            data=ReviewListSerializer(reviews, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ReviewAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed review information.
    
    Endpoint: GET /api/v1/human-reviews/admin/reviews/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
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


class ReviewAdminUpdateAPI(AuthAPI):
    """
    Admin: Update review.
    
    Endpoint: PUT /api/v1/human-reviews/admin/reviews/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def put(self, request, id):
        serializer = ReviewAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        update_fields = {}
        if 'status' in serializer.validated_data:
            update_fields['status'] = serializer.validated_data['status']
        if 'reviewer_id' in serializer.validated_data:
            update_fields['reviewer_id'] = serializer.validated_data['reviewer_id']
        
        version = serializer.validated_data.get('version')
        updated_by_id = str(request.user.id) if request.user.is_authenticated else None
        
        try:
            updated_review = ReviewService.update_review(
                id,
                updated_by_id=updated_by_id,
                version=version,
                **update_fields
            )
            if not updated_review:
                return self.api_response(
                    message=f"Review with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Review updated successfully.",
                data=ReviewSerializer(updated_review).data,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            # Handle version conflicts
            if 'version' in str(e).lower() or 'modified by another user' in str(e).lower():
                return self.api_response(
                    message="Review was modified by another user. Please refresh and try again.",
                    data={'error': str(e)},
                    status_code=status.HTTP_409_CONFLICT
                )
            return self.api_response(
                message="Validation error updating review.",
                data={'error': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


class ReviewAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete review.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/reviews/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        deleted = ReviewService.delete_review(id)
        if not deleted:
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


class BulkReviewOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on reviews.
    
    Endpoint: POST /api/v1/human-reviews/admin/reviews/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkReviewOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review_ids = serializer.validated_data['review_ids']
        operation = serializer.validated_data['operation']
        reviewer_id = serializer.validated_data.get('reviewer_id', None)
        assignment_strategy = serializer.validated_data.get('assignment_strategy', 'round_robin')
        
        results = {
            'success': [],
            'failed': []
        }
        
        for review_id in review_ids:
            if operation == 'assign':
                if reviewer_id:
                    updated_review = ReviewService.assign_reviewer(
                        str(review_id),
                        str(reviewer_id) if reviewer_id else None,
                        assignment_strategy
                    )
                else:
                    updated_review = ReviewService.assign_reviewer(
                        str(review_id),
                        None,
                        assignment_strategy
                    )
                if updated_review:
                    results['success'].append(str(review_id))
                else:
                    results['failed'].append({
                        'review_id': str(review_id),
                        'error': 'Review not found or failed to assign'
                    })
            elif operation == 'complete':
                updated_review = ReviewService.complete_review(str(review_id))
                if updated_review:
                    results['success'].append(str(review_id))
                else:
                    results['failed'].append({
                        'review_id': str(review_id),
                        'error': 'Review not found or failed to complete'
                    })
            elif operation == 'cancel':
                updated_review = ReviewService.cancel_review(str(review_id))
                if updated_review:
                    results['success'].append(str(review_id))
                else:
                    results['failed'].append({
                        'review_id': str(review_id),
                        'error': 'Review not found or failed to cancel'
                    })
            elif operation == 'delete':
                deleted = ReviewService.delete_review(str(review_id))
                if deleted:
                    results['success'].append(str(review_id))
                else:
                    results['failed'].append({
                        'review_id': str(review_id),
                        'error': 'Review not found or failed to delete'
                    })
        
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
