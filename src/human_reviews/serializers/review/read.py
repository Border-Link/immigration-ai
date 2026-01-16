from rest_framework import serializers
from human_reviews.models.review import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    case_user_email = serializers.EmailField(source='case.user.email', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id',
            'case',
            'reviewer',
            'reviewer_email',
            'case_user_email',
            'status',
            'assigned_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = (
            'id',
            'case',
            'reviewer',
            'reviewer_email',
            'case_user_email',
            'status',
            'assigned_at',
            'completed_at',
            'created_at',
            'updated_at',
        )


class ReviewListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing reviews."""
    
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True, allow_null=True)
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id',
            'case_id',
            'reviewer_email',
            'status',
            'assigned_at',
            'completed_at',
            'created_at',
        ]
        read_only_fields = (
            'id',
            'case_id',
            'reviewer_email',
            'status',
            'assigned_at',
            'completed_at',
            'created_at',
        )

