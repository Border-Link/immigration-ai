from rest_framework import serializers
from immigration_cases.models.case import Case


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
        read_only_fields = '__all__'


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
        read_only_fields = '__all__'

