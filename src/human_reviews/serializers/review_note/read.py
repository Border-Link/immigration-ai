from rest_framework import serializers
from human_reviews.models.review_note import ReviewNote


class ReviewNoteSerializer(serializers.ModelSerializer):
    """Serializer for ReviewNote model."""
    
    review_id = serializers.UUIDField(source='review.id', read_only=True)
    
    class Meta:
        model = ReviewNote
        fields = [
            'id',
            'review_id',
            'note',
            'is_internal',
            'created_at',
        ]
        read_only_fields = (
            'id',
            'review_id',
            'note',
            'is_internal',
            'created_at',
        )


class ReviewNoteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing review notes."""
    
    class Meta:
        model = ReviewNote
        fields = [
            'id',
            'note',
            'is_internal',
            'created_at',
        ]
        read_only_fields = (
            'id',
            'note',
            'is_internal',
            'created_at',
        )

