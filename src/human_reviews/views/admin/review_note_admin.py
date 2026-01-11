"""
Admin API Views for ReviewNote Management

Admin-only endpoints for managing review notes.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.serializers.review_note.read import ReviewNoteSerializer, ReviewNoteListSerializer
from human_reviews.serializers.review_note.admin import (
    ReviewNoteAdminListQuerySerializer,
    ReviewNoteAdminUpdateSerializer,
    BulkReviewNoteOperationSerializer,
)


class ReviewNoteAdminListAPI(AuthAPI):
    """
    Admin: Get list of all review notes with advanced filtering.
    
    Endpoint: GET /api/v1/human-reviews/admin/review-notes/
    Auth: Required (staff/superuser only)
    Query Params:
        - review_id: Filter by review ID
        - is_internal: Filter by internal status (true/false)
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = ReviewNoteAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        notes = ReviewNoteService.get_by_filters(
            review_id=str(query_serializer.validated_data.get('review_id')) if query_serializer.validated_data.get('review_id') else None,
            is_internal=query_serializer.validated_data.get('is_internal'),
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Review notes retrieved successfully.",
            data=ReviewNoteListSerializer(notes, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ReviewNoteAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed review note information.
    
    Endpoint: GET /api/v1/human-reviews/admin/review-notes/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review note"
    
    def get_entity_by_id(self, entity_id):
        """Get review note by ID."""
        return ReviewNoteService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return ReviewNoteSerializer


class ReviewNoteAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update review note.
    
    Endpoint: PUT /api/v1/human-reviews/admin/review-notes/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review note"
    
    def get_entity_by_id(self, entity_id):
        """Get review note by ID."""
        return ReviewNoteService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return ReviewNoteAdminUpdateSerializer
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return ReviewNoteSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the review note."""
        # Filter only the fields that are present in validated_data
        update_fields = {k: v for k, v in validated_data.items() if v is not None}
        return ReviewNoteService.update_review_note(str(entity.id), **update_fields)
    
    def put(self, request, id):
        """Override to support PUT method (base class uses PATCH)."""
        return self.patch(request, id)


class ReviewNoteAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete review note.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/review-notes/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review note"
    
    def get_entity_by_id(self, entity_id):
        """Get review note by ID."""
        return ReviewNoteService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the review note."""
        return ReviewNoteService.delete_review_note(str(entity.id))


class BulkReviewNoteOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on review notes.
    
    Endpoint: POST /api/v1/human-reviews/admin/review-notes/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk review note operation serializer."""
        return BulkReviewNoteOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Review note"
    
    def get_entity_by_id(self, entity_id):
        """Get review note by ID."""
        return ReviewNoteService.get_by_id(entity_id)
    
    def get_entity_ids(self, validated_data):
        """Override to use review_note_ids field name."""
        return validated_data.get('review_note_ids', [])
    
    def get_entity_id_field_name(self):
        """Override to use note_id field name."""
        return 'note_id'
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the review note."""
        if operation == 'delete':
            return ReviewNoteService.delete_review_note(str(entity.id))
        elif operation == 'set_internal':
            return ReviewNoteService.update_review_note(str(entity.id), is_internal=True)
        elif operation == 'set_public':
            return ReviewNoteService.update_review_note(str(entity.id), is_internal=False)
        else:
            raise ValueError(f"Invalid operation: {operation}")
