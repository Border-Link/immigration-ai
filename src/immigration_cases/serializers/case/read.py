from rest_framework import serializers
from immigration_cases.models.case import Case


class CaseListQuerySerializer(serializers.Serializer):
    """Serializer for validating CaseListAPI query parameters."""
    
    user_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Case.STATUS_CHOICES, required=False, allow_null=True)
    jurisdiction = serializers.ChoiceField(choices=Case.JURISDICTION_CHOICES, required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class CaseSerializer(serializers.ModelSerializer):
    """Serializer for Case model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id',
            'user',
            'user_email',
            'jurisdiction',
            'status',
            'version',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]


class CaseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing cases."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id',
            'user_email',
            'jurisdiction',
            'status',
            'created_at',
        ]
