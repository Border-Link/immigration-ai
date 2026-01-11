"""
Admin API Views for Review Management

Admin-only endpoints for managing reviews.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from human_reviews.services.review_service import ReviewService
from human_reviews.serializers.review.read import ReviewSerializer, ReviewListSerializer
from human_reviews.serializers.review.admin import (
    ReviewAdminListQuerySerializer,
    ReviewAdminUpdateSerializer,
    BulkReviewOperationSerializer,
)
from django.core.exceptions import ValidationError


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


class ReviewAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed review information.
    
    Endpoint: GET /api/v1/human-reviews/admin/reviews/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review"
    
    def get_entity_by_id(self, entity_id):
        """Get review by ID."""
        return ReviewService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return ReviewSerializer


class ReviewAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update review.
    
    Endpoint: PUT /api/v1/human-reviews/admin/reviews/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review"
    
    def get_entity_by_id(self, entity_id):
        """Get review by ID."""
        return ReviewService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return ReviewAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return ReviewSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the review with optimistic locking support."""
        update_fields = {}
        if 'status' in validated_data:
            update_fields['status'] = validated_data['status']
        if 'reviewer_id' in validated_data:
            update_fields['reviewer_id'] = validated_data['reviewer_id']
        
        version = validated_data.get('version')
        # Note: updated_by_id would need to be passed from request, but base class doesn't provide it
        # For now, we'll use None and let the service handle it
        updated_by_id = None
        
        return ReviewService.update_review(
            str(entity.id),
            updated_by_id=updated_by_id,
            version=version,
            **update_fields
        )
    
    def patch(self, request, id):
        """Override to handle optimistic locking and user context."""
        entity = self.get_entity_by_id(id)
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get updated_by_id from request
            updated_by_id = str(request.user.id) if request.user.is_authenticated else None
            validated_data = serializer.validated_data.copy()
            
            # Update entity with user context
            update_fields = {}
            if 'status' in validated_data:
                update_fields['status'] = validated_data['status']
            if 'reviewer_id' in validated_data:
                update_fields['reviewer_id'] = validated_data['reviewer_id']
            
            version = validated_data.get('version')
            updated_entity = ReviewService.update_review(
                str(entity.id),
                updated_by_id=updated_by_id,
                version=version,
                **update_fields
            )
            
            if updated_entity:
                response_serializer = self.get_response_serializer_class()
                if response_serializer:
                    response_data = response_serializer(updated_entity).data
                else:
                    response_data = serializer_class(updated_entity).data
                
                return self.api_response(
                    message=f"{self.get_entity_name()} updated successfully.",
                    data=response_data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to update {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error updating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, id):
        """Override to support PUT method (base class uses PATCH)."""
        return self.patch(request, id)


class ReviewAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete review.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/reviews/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review"
    
    def get_entity_by_id(self, entity_id):
        """Get review by ID."""
        return ReviewService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the review."""
        return ReviewService.delete_review(str(entity.id))


class BulkReviewOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on reviews.
    
    Endpoint: POST /api/v1/human-reviews/admin/reviews/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk review operation serializer."""
        return BulkReviewOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review"
    
    def get_entity_by_id(self, entity_id):
        """Get review by ID."""
        return ReviewService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the review."""
        reviewer_id = validated_data.get('reviewer_id')
        assignment_strategy = validated_data.get('assignment_strategy', 'round_robin')
        
        if operation == 'assign':
            return ReviewService.assign_reviewer(
                str(entity.id),
                str(reviewer_id) if reviewer_id else None,
                assignment_strategy
            )
        elif operation == 'complete':
            return ReviewService.complete_review(str(entity.id))
        elif operation == 'cancel':
            return ReviewService.cancel_review(str(entity.id))
        elif operation == 'delete':
            return ReviewService.delete_review(str(entity.id))
        else:
            raise ValueError(f"Invalid operation: {operation}")
