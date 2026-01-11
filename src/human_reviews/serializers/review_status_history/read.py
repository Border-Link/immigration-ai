from rest_framework import serializers
from human_reviews.models.review_status_history import ReviewStatusHistory


class ReviewStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for reading review status history data."""
    
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    review_id = serializers.UUIDField(source='review.id', read_only=True)
    
    class Meta:
        model = ReviewStatusHistory
        fields = [
            'id',
            'review_id',
            'previous_status',
            'new_status',
            'changed_by',
            'changed_by_email',
            'reason',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ReviewStatusHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing review status history entries."""
    
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    
    class Meta:
        model = ReviewStatusHistory
        fields = [
            'id',
            'previous_status',
            'new_status',
            'changed_by_email',
            'reason',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
