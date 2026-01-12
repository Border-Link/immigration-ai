from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.review_note_permission import ReviewNotePermission
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.serializers.review_note.create import ReviewNoteCreateSerializer
from human_reviews.serializers.review_note.read import ReviewNoteSerializer


class ReviewNoteCreateAPI(AuthAPI):
    """Create a new review note. Only reviewers can access."""
    permission_classes = [ReviewNotePermission]

    def post(self, request):
        serializer = ReviewNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_note = ReviewNoteService.create_review_note(
            review_id=serializer.validated_data.get('review_id'),
            note=serializer.validated_data.get('note'),
            is_internal=serializer.validated_data.get('is_internal', False)
        )

        if not review_note:
            return self.api_response(
                message="Error creating review note.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.api_response(
            message="Review note created successfully.",
            data=ReviewNoteSerializer(review_note).data,
            status_code=status.HTTP_201_CREATED
        )

