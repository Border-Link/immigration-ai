from rest_framework import serializers
from document_handling.selectors.case_document_selector import CaseDocumentSelector


class DocumentCheckCreateSerializer(serializers.Serializer):
    """Serializer for creating a document check."""
    
    case_document_id = serializers.UUIDField(required=True)
    check_type = serializers.ChoiceField(
        choices=['ocr', 'classification', 'validation', 'authenticity'],
        required=True
    )
    result = serializers.ChoiceField(
        choices=['passed', 'failed', 'warning', 'pending'],
        required=True
    )
    details = serializers.JSONField(required=False, allow_null=True)
    performed_by = serializers.CharField(required=False, max_length=50, allow_null=True, allow_blank=True)

    def validate_case_document_id(self, value):
        """Validate case document exists."""
        try:
            case_document = CaseDocumentSelector.get_by_id(value)
            if not case_document:
                raise serializers.ValidationError(f"Case document with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Case document with ID '{value}' not found.")
        return value

