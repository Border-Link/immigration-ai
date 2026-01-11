"""
Admin serializers for DocumentCheck operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer
from document_handling.models.document_check import DocumentCheck


class DocumentCheckAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating query parameters in admin list view."""
    case_document_id = serializers.UUIDField(required=False, allow_null=True)
    check_type = serializers.CharField(required=False, allow_null=True)
    result = serializers.CharField(required=False, allow_null=True)
    performed_by = serializers.CharField(required=False, allow_null=True)


class DocumentCheckAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing document checks in admin."""
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    case_id = serializers.UUIDField(source='case_document.case.id', read_only=True)
    
    class Meta:
        model = DocumentCheck
        fields = [
            'id',
            'case_document_id',
            'case_document_file_name',
            'case_id',
            'check_type',
            'result',
            'performed_by',
            'created_at',
        ]
        read_only_fields = '__all__'


class DocumentCheckAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed document check view in admin."""
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    case_document_status = serializers.CharField(source='case_document.status', read_only=True)
    case_id = serializers.UUIDField(source='case_document.case.id', read_only=True)
    case_user_email = serializers.EmailField(source='case_document.case.user.email', read_only=True)
    
    class Meta:
        model = DocumentCheck
        fields = [
            'id',
            'case_document_id',
            'case_document_file_name',
            'case_document_status',
            'case_id',
            'case_user_email',
            'check_type',
            'result',
            'details',
            'performed_by',
            'created_at',
        ]
        read_only_fields = '__all__'


class DocumentCheckAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating document check in admin."""
    result = serializers.ChoiceField(choices=DocumentCheck.RESULT_CHOICES, required=False)
    details = serializers.JSONField(required=False, allow_null=True)
    performed_by = serializers.CharField(required=False, allow_blank=True, max_length=50)


class BulkDocumentCheckOperationSerializer(serializers.Serializer):
    """Serializer for bulk document check operations."""
    check_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
