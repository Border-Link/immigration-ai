from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.review_note_permission import ReviewNotePermission
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.serializers.review_note.read import ReviewNoteSerializer
from human_reviews.serializers.review_note.update_delete import ReviewNoteUpdateSerializer


class ReviewNoteUpdateAPI(AuthAPI):
    """Update a review note. Only reviewers can access."""
    permission_classes = [ReviewNotePermission]

    def patch(self, request, id):
        serializer = ReviewNoteUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        note = ReviewNoteService.update_review_note(id, **serializer.validated_data)
        if not note:
            return self.api_response(
                message=f"Review note with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review note updated successfully.",
            data=ReviewNoteSerializer(note).data,
            status_code=status.HTTP_200_OK
        )


class ReviewNoteDeleteAPI(AuthAPI):
    """Delete a review note. Only reviewers can access."""
    permission_classes = [ReviewNotePermission]

    def delete(self, request, id):
        success = ReviewNoteService.delete_review_note(id)
        if not success:
            return self.api_response(
                message=f"Review note with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Review note deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )

