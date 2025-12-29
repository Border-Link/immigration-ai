from rest_framework import serializers
from rules_knowledge.models.visa_document_requirement import VisaDocumentRequirement


class VisaDocumentRequirementSerializer(serializers.ModelSerializer):
    """Serializer for VisaDocumentRequirement model."""
    
    rule_version_id = serializers.UUIDField(source='rule_version.id', read_only=True)
    visa_type_name = serializers.CharField(source='rule_version.visa_type.name', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    document_type_code = serializers.CharField(source='document_type.code', read_only=True)
    
    class Meta:
        model = VisaDocumentRequirement
        fields = [
            'id',
            'rule_version_id',
            'visa_type_name',
            'document_type',
            'document_type_name',
            'document_type_code',
            'mandatory',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class VisaDocumentRequirementListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing visa document requirements."""
    
    visa_type_name = serializers.CharField(source='rule_version.visa_type.name', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    
    class Meta:
        model = VisaDocumentRequirement
        fields = [
            'id',
            'visa_type_name',
            'document_type_name',
            'mandatory',
        ]
        read_only_fields = '__all__'

