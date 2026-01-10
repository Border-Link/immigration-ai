"""
Admin serializers for ProcessingJob operations.
"""
from rest_framework import serializers
from document_processing.models.processing_job import ProcessingJob


class ProcessingJobAdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing processing jobs in admin."""
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    case_id = serializers.UUIDField(source='case_document.case.id', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id',
            'case_document_id',
            'case_document_file_name',
            'case_id',
            'processing_type',
            'status',
            'priority',
            'retry_count',
            'max_retries',
            'celery_task_id',
            'created_by_email',
            'started_at',
            'completed_at',
            'created_at',
        ]
        read_only_fields = '__all__'


class ProcessingJobAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed processing job view in admin."""
    case_document_id = serializers.UUIDField(source='case_document.id', read_only=True)
    case_document_file_name = serializers.CharField(source='case_document.file_name', read_only=True)
    case_document_status = serializers.CharField(source='case_document.status', read_only=True)
    case_id = serializers.UUIDField(source='case_document.case.id', read_only=True)
    case_user_email = serializers.EmailField(source='case_document.case.user.email', read_only=True)
    created_by_id = serializers.UUIDField(source='created_by.id', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id',
            'case_document_id',
            'case_document_file_name',
            'case_document_status',
            'case_id',
            'case_user_email',
            'processing_type',
            'status',
            'priority',
            'retry_count',
            'max_retries',
            'celery_task_id',
            'error_message',
            'error_type',
            'metadata',
            'created_by_id',
            'created_by_email',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = '__all__'


class ProcessingJobAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating processing job in admin."""
    status = serializers.ChoiceField(choices=ProcessingJob.STATUS_CHOICES, required=False)
    priority = serializers.IntegerField(required=False, min_value=1, max_value=10)
    max_retries = serializers.IntegerField(required=False, min_value=0, max_value=10)
    error_message = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    error_type = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    metadata = serializers.JSONField(required=False, allow_null=True)


class BulkProcessingJobOperationSerializer(serializers.Serializer):
    """Serializer for bulk processing job operations."""
    job_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'delete',
        'cancel',
        'retry',
        'update_status',
        'update_priority',
    ])
    # For update_status operation
    status = serializers.ChoiceField(choices=ProcessingJob.STATUS_CHOICES, required=False)
    # For update_priority operation
    priority = serializers.IntegerField(required=False, min_value=1, max_value=10)
