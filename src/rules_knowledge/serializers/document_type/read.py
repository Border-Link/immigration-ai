from rest_framework import serializers
from rules_knowledge.models.document_type import DocumentType


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer for DocumentType model."""
    
    class Meta:
        model = DocumentType
        fields = [
            'id',
            'code',
            'name',
            'description',
            'is_active',
            'created_at',
            'updated_at',
        ]


class DocumentTypeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing document types."""
    
    class Meta:
        model = DocumentType
        fields = [
            'id',
            'code',
            'name',
            'is_active',
        ]

