from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.review_note_permission import ReviewNotePermission
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.serializers.review_note.read import ReviewNoteSerializer, ReviewNoteListSerializer


class ReviewNoteListAPI(AuthAPI):
    """Get list of review notes. Supports filtering by review_id. Only reviewers can access."""
    permission_classes = [ReviewNotePermission]

    def get(self, request):
        review_id = request.query_params.get('review_id', None)

        if review_id:
            notes = ReviewNoteService.get_by_review(review_id)
        else:
            notes = ReviewNoteService.get_all()

        return self.api_response(
            message="Review notes retrieved successfully.",
            data=ReviewNoteListSerializer(notes, many=True).data,
            status_code=status.HTTP_200_OK
        )


class ReviewNoteDetailAPI(AuthAPI):
    """Get review note by ID. Only reviewers can access."""
    permission_classes = [ReviewNotePermission]

    def get(self, request, id):
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


class ReviewNotePublicAPI(AuthAPI):
    """Get public (non-internal) notes for a review. Authenticated users can access."""
    permission_classes = [ReviewNotePermission]

    def get(self, request, review_id):
        notes = ReviewNoteService.get_public_by_review(review_id)

        return self.api_response(
            message="Public review notes retrieved successfully.",
            data=ReviewNoteListSerializer(notes, many=True).data,
            status_code=status.HTTP_200_OK
        )

