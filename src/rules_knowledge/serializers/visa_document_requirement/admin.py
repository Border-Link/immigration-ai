"""
Admin Serializers for VisaDocumentRequirement Management

Serializers for admin visa document requirement management operations.
"""
from rest_framework import serializers
from main_system.serializers.admin.base import BaseAdminListQuerySerializer


class VisaDocumentRequirementAdminListQuerySerializer(BaseAdminListQuerySerializer):
    """Serializer for validating VisaDocumentRequirementAdminListAPI query parameters."""
    
    rule_version_id = serializers.UUIDField(required=False, allow_null=True)
    document_type_id = serializers.UUIDField(required=False, allow_null=True)
    mandatory = serializers.BooleanField(required=False, allow_null=True)
    visa_type_id = serializers.UUIDField(required=False, allow_null=True)
    jurisdiction = serializers.CharField(required=False, allow_null=True, max_length=10)
    
    def to_internal_value(self, data):
        """Parse date strings to datetime objects and boolean values."""
        # Parse boolean strings before calling super
        if 'mandatory' in data and data.get('mandatory') is not None:
            if isinstance(data['mandatory'], str):
                data['mandatory'] = data['mandatory'].lower() == 'true'
        
        # Parse datetime strings using base class method
        return super().to_internal_value(data)


class VisaDocumentRequirementUpdateSerializer(serializers.Serializer):
    """Serializer for updating visa document requirement fields."""
    mandatory = serializers.BooleanField(required=False)
    conditional_logic = serializers.JSONField(required=False, allow_null=True)


class BulkVisaDocumentRequirementOperationSerializer(serializers.Serializer):
    """Serializer for bulk visa document requirement operations."""
    document_requirement_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(choices=[
        'set_mandatory',
        'set_optional',
        'delete',
    ])
