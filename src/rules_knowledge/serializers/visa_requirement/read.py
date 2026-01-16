from rest_framework import serializers
from rules_knowledge.models.visa_requirement import VisaRequirement


class VisaRequirementSerializer(serializers.ModelSerializer):
    """Serializer for VisaRequirement model."""
    
    rule_version_id = serializers.UUIDField(source='rule_version.id', read_only=True)
    visa_type_name = serializers.CharField(source='rule_version.visa_type.name', read_only=True)
    # API contract uses "is_active"; model uses "is_mandatory"
    is_active = serializers.BooleanField(source='is_mandatory', read_only=True)
    
    class Meta:
        model = VisaRequirement
        fields = [
            'id',
            'rule_version_id',
            'visa_type_name',
            'requirement_code',
            'description',
            'condition_expression',
            'is_active',
            'created_at',
            'updated_at',
        ]


class VisaRequirementListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing visa requirements."""
    
    visa_type_name = serializers.CharField(source='rule_version.visa_type.name', read_only=True)
    # API contract uses "is_active"; model uses "is_mandatory"
    is_active = serializers.BooleanField(source='is_mandatory', read_only=True)
    
    class Meta:
        model = VisaRequirement
        fields = [
            'id',
            'visa_type_name',
            'requirement_code',
            'description',
            'is_active',
        ]

