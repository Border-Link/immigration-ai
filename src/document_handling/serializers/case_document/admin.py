"""
Admin serializers for CaseDocument operations.
"""
from rest_framework import serializers
from document_handling.models.case_document import CaseDocument


class CaseDocumentAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing case documents in admin."""
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    case_user_email = serializers.EmailField(source='case.user.email', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    has_ocr_text = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = CaseDocument
        fields = [
            'id',
            'case_id',
            'case_user_email',
            'document_type_name',
            'file_name',
            'file_size',
            'mime_type',
            'status',
            'classification_confidence',
            'has_ocr_text',
            'expiry_date',
            'is_expired',
            'days_until_expiry',
            'content_validation_status',
            'uploaded_at',
        ]
        read_only_fields = '__all__'
    
    def get_has_ocr_text(self, obj):
        """Check if document has OCR text."""
        return bool(obj.ocr_text)
    
    def get_is_expired(self, obj):
        """Check if document expiry date has passed."""
        if not obj.expiry_date:
            return None
        from datetime import date
        return date.today() > obj.expiry_date
    
    def get_days_until_expiry(self, obj):
        """Calculate days until expiry."""
        if not obj.expiry_date:
            return None
        from datetime import date
        delta = obj.expiry_date - date.today()
        return delta.days


class CaseDocumentAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed case document view in admin."""
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    case_user_email = serializers.EmailField(source='case.user.email', read_only=True)
    case_user_id = serializers.UUIDField(source='case.user.id', read_only=True)
    document_type_id = serializers.UUIDField(source='document_type.id', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    content_validation_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = CaseDocument
        fields = [
            'id',
            'case_id',
            'case_user_email',
            'case_user_id',
            'document_type_id',
            'document_type_name',
            'file_path',
            'file_name',
            'file_size',
            'mime_type',
            'status',
            'ocr_text',
            'classification_confidence',
            'expiry_date',
            'is_expired',
            'days_until_expiry',
            'extracted_metadata',
            'content_validation_status',
            'content_validation_details',
            'content_validation_summary',
            'uploaded_at',
            'updated_at',
        ]
        read_only_fields = '__all__'
    
    def get_is_expired(self, obj):
        """Check if document expiry date has passed."""
        if not obj.expiry_date:
            return None
        from datetime import date
        return date.today() > obj.expiry_date
    
    def get_days_until_expiry(self, obj):
        """Calculate days until expiry."""
        if not obj.expiry_date:
            return None
        from datetime import date
        delta = obj.expiry_date - date.today()
        return delta.days
    
    def get_content_validation_summary(self, obj):
        """Get human-readable content validation summary."""
        if not obj.content_validation_details:
            return None
        from document_handling.services.document_content_validation_service import DocumentContentValidationService
        return DocumentContentValidationService.get_validation_summary(obj.content_validation_details)


class CaseDocumentAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating case document in admin."""
    document_type_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=CaseDocument.STATUS_CHOICES, required=False)
    classification_confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, allow_null=True)
    ocr_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    content_validation_status = serializers.ChoiceField(
        choices=['pending', 'passed', 'failed', 'warning'],
        required=False
    )
    content_validation_details = serializers.JSONField(required=False, allow_null=True)
    extracted_metadata = serializers.JSONField(required=False, allow_null=True)


class BulkCaseDocumentOperationSerializer(serializers.Serializer):
    """Serializer for bulk case document operations."""
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'update_status',
        'reprocess_ocr',
        'reprocess_classification',
        'reprocess_validation',
        'reprocess_full',
    ])
    # For update_status operation
    status = serializers.ChoiceField(choices=CaseDocument.STATUS_CHOICES, required=False)
