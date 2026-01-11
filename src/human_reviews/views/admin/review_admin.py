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
    ReviewAdminUpdateSerializer,
    BulkReviewOperationSerializer,
)
from django.utils.dateparse import parse_datetime

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
        case_id = request.query_params.get('case_id', None)
        reviewer_id = request.query_params.get('reviewer_id', None)
        status_filter = request.query_params.get('status', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        assigned_date_from = request.query_params.get('assigned_date_from', None)
        assigned_date_to = request.query_params.get('assigned_date_to', None)
        completed_date_from = request.query_params.get('completed_date_from', None)
        completed_date_to = request.query_params.get('completed_date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            parsed_assigned_date_from = parse_datetime(assigned_date_from) if assigned_date_from and isinstance(assigned_date_from, str) else assigned_date_from
            parsed_assigned_date_to = parse_datetime(assigned_date_to) if assigned_date_to and isinstance(assigned_date_to, str) else assigned_date_to
            parsed_completed_date_from = parse_datetime(completed_date_from) if completed_date_from and isinstance(completed_date_from, str) else completed_date_from
            parsed_completed_date_to = parse_datetime(completed_date_to) if completed_date_to and isinstance(completed_date_to, str) else completed_date_to
            
            # Use service method with filters
            reviews = ReviewService.get_by_filters(
                case_id=case_id,
                reviewer_id=reviewer_id,
                status=status_filter,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                assigned_date_from=parsed_assigned_date_from,
                assigned_date_to=parsed_assigned_date_to,
                completed_date_from=parsed_completed_date_from,
                completed_date_to=parsed_completed_date_to
            )
            
            return self.api_response(
                message="Reviews retrieved successfully.",
                data=ReviewListSerializer(reviews, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving reviews: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving reviews.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed review information.
    
    Endpoint: GET /api/v1/human-reviews/admin/reviews/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
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
        except Exception as e:
            logger.error(f"Error retrieving review {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving review.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            review = ReviewService.get_by_id(id)
            if not review:
                return self.api_response(
                    message=f"Review with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            update_fields = {}
            if 'status' in serializer.validated_data:
                update_fields['status'] = serializer.validated_data['status']
            if 'reviewer_id' in serializer.validated_data:
                update_fields['reviewer_id'] = serializer.validated_data['reviewer_id']
            
            updated_review = ReviewService.update_review(id, **update_fields)
            if not updated_review:
                return self.api_response(
                    message="Error updating review.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Review updated successfully.",
                data=ReviewSerializer(updated_review).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating review {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating review.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete review.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/reviews/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            review = ReviewService.get_by_id(id)
            if not review:
                return self.api_response(
                    message=f"Review with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = ReviewService.delete_review(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting review.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Review deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting review {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting review.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        
        try:
            for review_id in review_ids:
                try:
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
                except Exception as e:
                    results['failed'].append({
                        'review_id': str(review_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error performing bulk operation on reviews: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
