from rest_framework import serializers
from rules_knowledge.models.visa_rule_version import VisaRuleVersion


class VisaRuleVersionSerializer(serializers.ModelSerializer):
    """Serializer for VisaRuleVersion model."""
    
    visa_type_name = serializers.CharField(source='visa_type.name', read_only=True)
    visa_type_code = serializers.CharField(source='visa_type.code', read_only=True)
    
    class Meta:
        model = VisaRuleVersion
        fields = [
            'id',
            'visa_type',
            'visa_type_name',
            'visa_type_code',
            'version_number',
            'effective_from',
            'effective_to',
            'source_document_version',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class VisaRuleVersionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing visa rule versions."""
    
    visa_type_name = serializers.CharField(source='visa_type.name', read_only=True)
    
    class Meta:
        model = VisaRuleVersion
        fields = [
            'id',
            'visa_type_name',
            'version_number',
            'effective_from',
            'effective_to',
        ]
        read_only_fields = '__all__'

