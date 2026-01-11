from rest_framework import serializers


class ReviewReassignSerializer(serializers.Serializer):
    """Serializer for reassigning a review to a different reviewer."""
    
    new_reviewer_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_new_reviewer_id(self, value):
        """Validate reviewer exists, has reviewer role, and is staff or admin."""
        from users_access.selectors.user_selector import UserSelector
        try:
            reviewer = UserSelector.get_by_id(value)
            if not reviewer:
                raise serializers.ValidationError(f"Reviewer with ID '{value}' not found.")
            if reviewer.role != 'reviewer':
                raise serializers.ValidationError(f"User with ID '{value}' does not have reviewer role.")
            if not (reviewer.is_staff or reviewer.is_superuser):
                raise serializers.ValidationError(f"User with ID '{value}' is not staff or admin.")
        except Exception as e:
            raise serializers.ValidationError(f"Reviewer with ID '{value}' not found.")
        return value


class ReviewEscalateSerializer(serializers.Serializer):
    """Serializer for escalating a review."""
    
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    priority = serializers.ChoiceField(choices=['high', 'urgent'], default='high', required=False)


class ReviewApproveSerializer(serializers.Serializer):
    """Serializer for approving a review."""
    
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class ReviewRejectSerializer(serializers.Serializer):
    """Serializer for rejecting a review."""
    
    reason = serializers.CharField(required=True, max_length=500)


class ReviewRequestChangesSerializer(serializers.Serializer):
    """Serializer for requesting changes on a review."""
    
    reason = serializers.CharField(required=True, max_length=500)
