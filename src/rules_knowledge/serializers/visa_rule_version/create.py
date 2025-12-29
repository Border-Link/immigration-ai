from rest_framework import serializers
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from data_ingestion.selectors.document_version_selector import DocumentVersionSelector


class VisaRuleVersionCreateSerializer(serializers.Serializer):
    """Serializer for creating a visa rule version."""
    
    visa_type_id = serializers.UUIDField(required=True)
    effective_from = serializers.DateTimeField(required=True)
    effective_to = serializers.DateTimeField(required=False, allow_null=True)
    source_document_version_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_visa_type_id(self, value):
        """Validate visa type exists."""
        try:
            visa_type = VisaTypeSelector.get_by_id(value)
            if not visa_type:
                raise serializers.ValidationError(f"Visa type with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Visa type with ID '{value}' not found.")
        return value

    def validate_source_document_version_id(self, value):
        """Validate document version exists."""
        if value:
            try:
                doc_version = DocumentVersionSelector.get_by_id(value)
                if not doc_version:
                    raise serializers.ValidationError(f"Document version with ID '{value}' not found.")
            except Exception as e:
                raise serializers.ValidationError(f"Document version with ID '{value}' not found.")
        return value

