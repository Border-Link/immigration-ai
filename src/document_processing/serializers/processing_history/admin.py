"""
Admin serializers for ProcessingHistory operations.
"""
from rest_framework import serializers
from document_processing.models.processing_history import ProcessingHistory


class ProcessingHistoryAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing processing history in admin."""
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    processing_job_id = serializers.UUIDField(source='processing_job.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ProcessingHistory
        fields = [
            'id',
            'case_document_id',
            'case_document_file_name',
            'processing_job_id',
            'action',
            'status',
            'error_type',
            'processing_time_ms',
            'user_email',
            'created_at',
        ]
        read_only_fields = '__all__'


class ProcessingHistoryAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed processing history view in admin."""
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    case_id = serializers.UUIDField(source='case_document.case.id', read_only=True)
    processing_job_id = serializers.UUIDField(source='processing_job.id', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ProcessingHistory
        fields = [
            'id',
            'case_document_id',
            'case_document_file_name',
            'case_id',
            'processing_job_id',
            'action',
            'status',
            'message',
            'metadata',
            'error_type',
            'error_message',
            'processing_time_ms',
            'user_id',
            'user_email',
            'created_at',
        ]
        read_only_fields = '__all__'


class BulkProcessingHistoryOperationSerializer(serializers.Serializer):
    """Serializer for bulk processing history operations."""
    history_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
    ])
