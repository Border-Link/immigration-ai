from rest_framework import serializers
from immigration_cases.models.case_fact import CaseFact


class CaseFactListQuerySerializer(serializers.Serializer):
    """Serializer for validating CaseFactListAPI query parameters."""
    
    case_id = serializers.UUIDField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class CaseFactSerializer(serializers.ModelSerializer):
    """Serializer for CaseFact model."""
    
    class Meta:
        model = CaseFact
        fields = [
            'id',
            'case',
            'fact_key',
            'fact_value',
            'source',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class CaseFactListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing case facts."""
    
    class Meta:
        model = CaseFact
        fields = [
            'id',
            'case',
            'fact_key',
            'fact_value',
            'source',
            'created_at',
        ]
        read_only_fields = '__all__'
