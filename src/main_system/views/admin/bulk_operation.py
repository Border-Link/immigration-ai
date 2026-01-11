"""
Base Bulk Operation API View

Generic base class for bulk operation views to reduce code duplication.
"""
import logging
from typing import Dict, List, Any, Optional
from rest_framework import status
from main_system.base.auth_api import AuthAPI

logger = logging.getLogger('django')


class BaseBulkOperationAPI(AuthAPI):
    """
    Base class for bulk operation views.
    
    Provides common structure for bulk operations:
    - Serializer validation
    - Results tracking (success/failed)
    - Error handling
    - Response formatting
    
    Child classes should:
    - Override get_serializer_class() to return the bulk operation serializer
    - Override get_entity_name() to return human-readable entity name
    - Override get_entity_by_id(id) to fetch the entity
    - Override execute_operation(entity, operation, validated_data) to perform the operation
    - Optionally override get_success_data(entity, operation_result) to customize success response
    """
    
    def get_serializer_class(self):
        """
        Get the serializer class for bulk operations.
        
        Must be overridden by child classes.
        """
        raise NotImplementedError("Child classes must implement get_serializer_class()")
    
    def post(self, request):
        """
        Execute bulk operation.
        
        Expected serializer fields:
        - {entity_name}_ids: List[UUID] - List of entity IDs
        - operation: str - Operation to perform
        - Additional fields as needed for the operation
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        # Get entity IDs and operation
        entity_ids = self.get_entity_ids(validated_data)
        operation = validated_data['operation']
        
        # Initialize results
        results = {
            'success': [],
            'failed': []
        }
        
        # Process each entity
        for entity_id in entity_ids:
            try:
                # Get entity
                entity = self.get_entity_by_id(str(entity_id))
                if not entity:
                    results['failed'].append({
                        self.get_entity_id_field_name(): str(entity_id),
                        'error': f'{self.get_entity_name()} not found'
                    })
                    continue
                
                # Execute operation
                operation_result = self.execute_operation(
                    entity=entity,
                    operation=operation,
                    validated_data=validated_data
                )
                
                if operation_result:
                    success_data = self.get_success_data(entity, operation_result)
                    results['success'].append(success_data)
                else:
                    results['failed'].append({
                        self.get_entity_id_field_name(): str(entity_id),
                        'error': f'Failed to execute operation: {operation}'
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {self.get_entity_name()} {entity_id}: {e}", exc_info=True)
                results['failed'].append({
                    self.get_entity_id_field_name(): str(entity_id),
                    'error': str(e)
                })
        
        # Return response
        return self.api_response(
            message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )
    
    def get_entity_ids(self, validated_data: Dict) -> List:
        """
        Extract entity IDs from validated data.
        
        Default implementation looks for '{entity_name}_ids' field.
        Override if field name differs.
        """
        entity_name = self.get_entity_name().lower().replace(' ', '_')
        field_name = f'{entity_name}_ids'
        return validated_data.get(field_name, [])
    
    def get_entity_id_field_name(self) -> str:
        """
        Get the field name for entity ID in error responses.
        
        Default: '{entity_name}_id'
        """
        entity_name = self.get_entity_name().lower().replace(' ', '_')
        return f'{entity_name}_id'
    
    def get_entity_name(self) -> str:
        """
        Get the human-readable entity name.
        
        Must be overridden by child classes.
        """
        raise NotImplementedError("Child classes must implement get_entity_name()")
    
    def get_entity_by_id(self, entity_id: str):
        """
        Get entity by ID.
        
        Must be overridden by child classes.
        """
        raise NotImplementedError("Child classes must implement get_entity_by_id(entity_id)")
    
    def execute_operation(self, entity: Any, operation: str, validated_data: Dict) -> Optional[Any]:
        """
        Execute the operation on the entity.
        
        Must be overridden by child classes.
        
        Args:
            entity: The entity to operate on
            operation: The operation to perform
            validated_data: All validated data from serializer
            
        Returns:
            Operation result (truthy if successful, falsy if failed)
        """
        raise NotImplementedError("Child classes must implement execute_operation(entity, operation, validated_data)")
    
    def get_success_data(self, entity: Any, operation_result: Any) -> Any:
        """
        Get data to include in success results.
        
        Default: Returns entity ID as string.
        Override to return serialized entity data or custom response.
        
        Args:
            entity: The entity that was operated on
            operation_result: The result from execute_operation()
            
        Returns:
            Data to include in results['success']
        """
        return str(entity.id)
