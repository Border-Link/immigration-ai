"""
Admin API Views for ReviewNote Management

Admin-only endpoints for managing review notes.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.serializers.review_note.read import ReviewNoteSerializer, ReviewNoteListSerializer
from human_reviews.serializers.review_note.admin import (
    ReviewNoteAdminUpdateSerializer,
    BulkReviewNoteOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
        review_id = request.query_params.get('review_id', None)
        is_internal = request.query_params.get('is_internal', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            is_internal_bool = is_internal.lower() == 'true' if is_internal is not None else None
            
            # Use service method with filters
            notes = ReviewNoteService.get_by_filters(
                review_id=review_id,
                is_internal=is_internal_bool,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Review notes retrieved successfully.",
                data=ReviewNoteListSerializer(notes, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving review notes: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving review notes.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewNoteAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed review note information.
    
    Endpoint: GET /api/v1/human-reviews/admin/review-notes/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            note = ReviewNoteService.get_by_id(id)
            if not note:
                return self.api_response(
                    message=f"Review note with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Review note retrieved successfully.",
                data=ReviewNoteSerializer(note).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving review note {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving review note.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewNoteAdminUpdateAPI(AuthAPI):
    """
    Admin: Update review note.
    
    Endpoint: PUT /api/v1/human-reviews/admin/review-notes/<id>/update/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def put(self, request, id):
        serializer = ReviewNoteAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            note = ReviewNoteService.get_by_id(id)
            if not note:
                return self.api_response(
                    message=f"Review note with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            update_fields = {}
            if 'note' in serializer.validated_data:
                update_fields['note'] = serializer.validated_data['note']
            if 'is_internal' in serializer.validated_data:
                update_fields['is_internal'] = serializer.validated_data['is_internal']
            
            updated_note = ReviewNoteService.update_review_note(id, **update_fields)
            if not updated_note:
                return self.api_response(
                    message="Error updating review note.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Review note updated successfully.",
                data=ReviewNoteSerializer(updated_note).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating review note {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error updating review note.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewNoteAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete review note.
    
    Endpoint: DELETE /api/v1/human-reviews/admin/review-notes/<id>/delete/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            note = ReviewNoteService.get_by_id(id)
            if not note:
                return self.api_response(
                    message=f"Review note with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = ReviewNoteService.delete_review_note(id)
            if not deleted:
                return self.api_response(
                    message="Error deleting review note.",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.api_response(
                message="Review note deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting review note {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting review note.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkReviewNoteOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on review notes.
    
    Endpoint: POST /api/v1/human-reviews/admin/review-notes/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkReviewNoteOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        note_ids = serializer.validated_data['review_note_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for note_id in note_ids:
                try:
                    if operation == 'delete':
                        deleted = ReviewNoteService.delete_review_note(str(note_id))
                        if deleted:
                            results['success'].append(str(note_id))
                        else:
                            results['failed'].append({
                                'note_id': str(note_id),
                                'error': 'Review note not found or failed to delete'
                            })
                    elif operation == 'set_internal':
                        updated_note = ReviewNoteService.update_review_note(str(note_id), is_internal=True)
                        if updated_note:
                            results['success'].append(str(note_id))
                        else:
                            results['failed'].append({
                                'note_id': str(note_id),
                                'error': 'Review note not found or failed to update'
                            })
                    elif operation == 'set_public':
                        updated_note = ReviewNoteService.update_review_note(str(note_id), is_internal=False)
                        if updated_note:
                            results['success'].append(str(note_id))
                        else:
                            results['failed'].append({
                                'note_id': str(note_id),
                                'error': 'Review note not found or failed to update'
                            })
                except Exception as e:
                    results['failed'].append({
                        'note_id': str(note_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error performing bulk operation on review notes: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
