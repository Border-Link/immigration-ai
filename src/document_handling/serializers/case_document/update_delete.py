from rest_framework import serializers
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector


class CaseDocumentUpdateSerializer(serializers.Serializer):
    """Serializer for updating a case document."""
    
    document_type_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=['uploaded', 'processing', 'verified', 'rejected'],
        required=False
    )

    def validate_document_type_id(self, value):
        """Validate document type exists."""
        if value:
            try:
                document_type = DocumentTypeSelector.get_by_id(value)
                if not document_type or not document_type.is_active:
                    raise serializers.ValidationError(f"Document type with ID '{value}' not found or inactive.")
            except Exception as e:
                raise serializers.ValidationError(f"Document type with ID '{value}' not found.")
        return value


class CaseDocumentDeleteSerializer(serializers.Serializer):
    """Serializer for deleting a case document."""
    
    id = serializers.UUIDField(required=True)

