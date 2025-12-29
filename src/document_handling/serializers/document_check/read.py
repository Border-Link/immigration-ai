from rest_framework import serializers
from document_handling.models.document_check import DocumentCheck


class DocumentCheckSerializer(serializers.ModelSerializer):
    """Serializer for reading document check data."""
    
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    
    class Meta:
        model = DocumentCheck
        fields = [
            'id',
            'case_document',
            'case_document_id',
            'case_document_file_name',
            'check_type',
            'result',
            'details',
            'performed_by',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DocumentCheckListSerializer(serializers.ModelSerializer):
    """Serializer for listing document checks."""
    
    class Meta:
        model = DocumentCheck
        fields = [
            'id',
            'check_type',
            'result',
            'created_at',
        ]

