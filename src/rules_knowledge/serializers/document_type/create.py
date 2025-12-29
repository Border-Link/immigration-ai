from rest_framework import serializers
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector


class DocumentTypeCreateSerializer(serializers.Serializer):
    """Serializer for creating a document type."""
    
    code = serializers.CharField(required=True, max_length=100)
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_code(self, value):
        """Validate code is unique."""
        value = value.strip().upper()
        try:
            DocumentTypeSelector.get_by_code(value)
            raise serializers.ValidationError(f"Document type with code '{value}' already exists.")
        except Exception:
            # DoesNotExist is expected
            pass
        return value

