from rest_framework import serializers


class RuleValidationTaskUpdateSerializer(serializers.Serializer):
    """Serializer for updating a rule validation task."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'approved', 'rejected', 'needs_revision'],
        required=False
    )
    reviewer_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    assigned_to = serializers.UUIDField(required=False, allow_null=True)

    def validate_assigned_to(self, value):
        """Validate assigned reviewer exists."""
        if value:
            from users_access.selectors.user_selector import UserSelector
            try:
                UserSelector.get_by_id(value)
            except Exception:
                raise serializers.ValidationError("Reviewer not found")
        return value


class RuleValidationTaskAssignSerializer(serializers.Serializer):
    """Serializer for assigning a reviewer to a validation task."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    reviewer_id = serializers.UUIDField(required=True)

    def validate_reviewer_id(self, value):
        """Validate reviewer exists."""
        from users_access.selectors.user_selector import UserSelector
        try:
            reviewer = UserSelector.get_by_id(value)
            if not reviewer:
                raise serializers.ValidationError("Reviewer not found")
            # Check if user is staff/admin
            if not (reviewer.is_staff or reviewer.is_superuser):
                raise serializers.ValidationError("Reviewer must be staff or admin")
        except Exception as e:
            raise serializers.ValidationError(f"Invalid reviewer: {str(e)}")
        return value


class RuleValidationTaskApproveSerializer(serializers.Serializer):
    """Serializer for approving a validation task."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    reviewer_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class RuleValidationTaskRejectSerializer(serializers.Serializer):
    """Serializer for rejecting a validation task."""
    
    version = serializers.IntegerField(required=False, help_text="Version for optimistic locking")
    reviewer_notes = serializers.CharField(required=True, allow_blank=False)

