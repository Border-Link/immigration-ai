from rest_framework import serializers


class CaseStatusHistoryListQuerySerializer(serializers.Serializer):
    """Serializer for validating CaseStatusHistoryListAPI query parameters."""
    
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
