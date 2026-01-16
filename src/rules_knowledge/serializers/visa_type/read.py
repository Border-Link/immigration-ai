from rest_framework import serializers
from rules_knowledge.models.visa_type import VisaType


class VisaTypeSerializer(serializers.ModelSerializer):
    """Serializer for VisaType model."""
    
    class Meta:
        model = VisaType
        fields = [
            'id',
            'jurisdiction',
            'code',
            'name',
            'description',
            'is_active',
            'created_at',
            'updated_at',
        ]


class VisaTypeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing visa types."""
    
    class Meta:
        model = VisaType
        fields = [
            'id',
            'jurisdiction',
            'code',
            'name',
            'is_active',
        ]

