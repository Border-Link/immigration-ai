from rest_framework import serializers
from document_handling.models.case_document import CaseDocument


class CaseDocumentSerializer(serializers.ModelSerializer):
    """Serializer for reading case document data."""
    
    case_id = serializers.UUIDField(source='case.id', read_only=True)
    document_type_code = serializers.CharField(source='document_type.code', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    checks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CaseDocument
        fields = [
            'id',
            'case',
            'case_id',
            'document_type',
            'document_type_code',
            'document_type_name',
            'file_path',
            'file_name',
            'file_size',
            'mime_type',
            'status',
            'checks_count',
            'uploaded_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at']
    
    def get_checks_count(self, obj):
        """Get count of checks for this document."""
        if hasattr(obj, 'checks'):
            return obj.checks.count()
        return 0


class CaseDocumentListSerializer(serializers.ModelSerializer):
    """Serializer for listing case documents."""
    
    document_type_code = serializers.CharField(source='document_type.code', read_only=True)
    
    class Meta:
        model = CaseDocument
        fields = [
            'id',
            'file_name',
            'document_type_code',
            'status',
            'uploaded_at',
        ]

