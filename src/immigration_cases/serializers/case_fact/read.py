from rest_framework import serializers
from immigration_cases.models.case_fact import CaseFact


class CaseFactSerializer(serializers.ModelSerializer):
    """Serializer for CaseFact model."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = CaseFact
        fields = [
            'id',
            'case_id',
            'fact_key',
            'fact_value',
            'source',
            'created_at',
        ]
        read_only_fields = '__all__'


class CaseFactListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing case facts."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    
    class Meta:
        model = CaseFact
        fields = [
            'id',
            'case_id',
            'fact_key',
            'fact_value',
            'source',
            'created_at',
        ]
        read_only_fields = '__all__'

