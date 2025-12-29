from rest_framework import serializers
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector


class VisaDocumentRequirementCreateSerializer(serializers.Serializer):
    """Serializer for creating a visa document requirement."""
    
    rule_version_id = serializers.UUIDField(required=True)
    document_type_id = serializers.UUIDField(required=True)
    mandatory = serializers.BooleanField(required=False, default=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_rule_version_id(self, value):
        """Validate rule version exists."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(value)
            if not rule_version:
                raise serializers.ValidationError(f"Rule version with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Rule version with ID '{value}' not found.")
        return value

    def validate_document_type_id(self, value):
        """Validate document type exists."""
        try:
            document_type = DocumentTypeSelector.get_by_id(value)
            if not document_type or not document_type.is_active:
                raise serializers.ValidationError(f"Document type with ID '{value}' not found or inactive.")
        except Exception as e:
            raise serializers.ValidationError(f"Document type with ID '{value}' not found.")
        return value

