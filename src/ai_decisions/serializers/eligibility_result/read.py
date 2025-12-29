from rest_framework import serializers
from ai_decisions.models.eligibility_result import EligibilityResult


class EligibilityResultSerializer(serializers.ModelSerializer):
    """Serializer for EligibilityResult model."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    visa_type_name = serializers.CharField(source='visa_type.name', read_only=True)
    visa_type_code = serializers.CharField(source='visa_type.code', read_only=True)
    rule_version_number = serializers.IntegerField(source='rule_version.version_number', read_only=True)
    
    class Meta:
        model = EligibilityResult
        fields = [
            'id',
            'case_id',
            'visa_type_name',
            'visa_type_code',
            'rule_version_number',
            'outcome',
            'confidence',
            'reasoning_summary',
            'missing_facts',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class EligibilityResultListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing eligibility results."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    visa_type_name = serializers.CharField(source='visa_type.name', read_only=True)
    
    class Meta:
        model = EligibilityResult
        fields = [
            'id',
            'case_id',
            'visa_type_name',
            'outcome',
            'confidence',
            'created_at',
        ]
        read_only_fields = '__all__'

