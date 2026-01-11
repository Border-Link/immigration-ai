"""
Base Bulk Operation Serializers

Base classes for bulk operation serializers.
"""
from rest_framework import serializers


class BaseBulkOperationSerializer(serializers.Serializer):
    """
    Base class for bulk operation serializers.
    
    Provides common fields:
    - operation_ids: List of UUIDs
    - operation: ChoiceField for operation type
    
    Child classes should:
    - Override operation_ids field name if different (e.g., case_ids, user_ids)
    - Add operation-specific fields
    - Override operation choices
    """
    
    operation = serializers.ChoiceField(
        choices=[],
        help_text="Operation to perform on the entities"
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize with configurable entity ID field name."""
        entity_id_field_name = kwargs.pop('entity_id_field_name', 'entity_ids')
        super().__init__(*args, **kwargs)
        
        # Add dynamic entity IDs field
        self.fields[entity_id_field_name] = serializers.ListField(
            child=serializers.UUIDField(),
            min_length=1,
            max_length=100,
            help_text=f"List of {entity_id_field_name.replace('_ids', '')} IDs to operate on"
        )
