from rest_framework import serializers
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector


class CaseDocumentCreateSerializer(serializers.Serializer):
    """Serializer for creating a case document."""
    
    case_id = serializers.UUIDField(required=True)
    document_type_id = serializers.UUIDField(required=True)
    file_name = serializers.CharField(required=True, max_length=255)
    file_size = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    mime_type = serializers.CharField(required=False, max_length=100, allow_null=True, allow_blank=True)

    def validate_case_id(self, value):
        """Validate case exists."""
        try:
            from immigration_cases.models.case import Case
            case = Case.objects.get(id=value)
            if not case:
                raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        except Case.DoesNotExist:
            raise serializers.ValidationError(f"Case with ID '{value}' not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Error validating case: {str(e)}")
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

    def validate_file_name(self, value):
        """Validate file name."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("File name cannot be empty.")
        # Check file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if not any(value.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("File must be PDF, JPG, or PNG.")
        return value

    def validate_file_size(self, value):
        """Validate file size (max 10MB)."""
        if value and value > 10 * 1024 * 1024:  # 10MB in bytes
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        return value

