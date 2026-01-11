"""
Base Admin API Views

Generic base classes for admin views to reduce code duplication.
"""
import logging
from typing import Optional, Any
from rest_framework import status
from main_system.base.auth_api import AuthAPI

logger = logging.getLogger('django')


class BaseAdminDetailAPI(AuthAPI):
    """
    Base class for admin detail views.
    
    Provides common structure for getting a single entity by ID.
    
    Child classes should:
    - Override get_entity_by_id(id) to fetch the entity
    - Override get_serializer_class() to return the detail serializer
    """
    
    def get(self, request, id):
        """Get entity detail by ID."""
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(entity)
        
        return self.api_response(
            message=f"{self.get_entity_name()} retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    def get_entity_name(self) -> str:
        """Get the human-readable entity name. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_name()")
    
    def get_entity_by_id(self, entity_id: str):
        """Get entity by ID. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_by_id(entity_id)")
    
    def get_serializer_class(self):
        """Get serializer class for detail view. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_serializer_class()")


class BaseAdminDeleteAPI(AuthAPI):
    """
    Base class for admin delete views.
    
    Provides common structure for deleting an entity by ID.
    
    Child classes should:
    - Override get_entity_by_id(id) to fetch the entity
    - Override delete_entity(entity) to perform the deletion
    """
    
    def delete(self, request, id):
        """Delete entity by ID."""
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            deleted = self.delete_entity(entity)
            if deleted:
                return self.api_response(
                    message=f"{self.get_entity_name()} deleted successfully.",
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to delete {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error deleting {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error deleting {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_entity_name(self) -> str:
        """Get the human-readable entity name. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_name()")
    
    def get_entity_by_id(self, entity_id: str):
        """Get entity by ID. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_by_id(entity_id)")
    
    def delete_entity(self, entity: Any) -> bool:
        """Delete the entity. Must be overridden."""
        raise NotImplementedError("Child classes must implement delete_entity(entity)")


class BaseAdminActivateAPI(AuthAPI):
    """
    Base class for admin activate/deactivate views.
    
    Provides common structure for activating or deactivating an entity.
    
    Child classes should:
    - Override get_entity_by_id(id) to fetch the entity
    - Override activate_entity(entity, is_active) to perform activation
    """
    
    def post(self, request, id):
        """Activate or deactivate entity by ID."""
        from main_system.serializers.admin.base import ActivateSerializer
        
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_active = serializer.validated_data['is_active']
        
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            updated = self.activate_entity(entity, is_active)
            if updated:
                action = "activated" if is_active else "deactivated"
                return self.api_response(
                    message=f"{self.get_entity_name()} {action} successfully.",
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to update {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error updating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_entity_name(self) -> str:
        """Get the human-readable entity name. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_name()")
    
    def get_entity_by_id(self, entity_id: str):
        """Get entity by ID. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_by_id(entity_id)")
    
    def activate_entity(self, entity: Any, is_active: bool) -> bool:
        """Activate or deactivate the entity. Must be overridden."""
        raise NotImplementedError("Child classes must implement activate_entity(entity, is_active)")


class BaseAdminUpdateAPI(AuthAPI):
    """
    Base class for admin update views.
    
    Provides common structure for updating an entity by ID.
    
    Child classes should:
    - Override get_entity_by_id(id) to fetch the entity
    - Override get_serializer_class() to return the update serializer
    - Override update_entity(entity, validated_data) to perform the update
    """
    
    def patch(self, request, id):
        """Update entity by ID."""
        entity = self.get_entity_by_id(str(id))
        if not entity:
            return self.api_response(
                message=f"{self.get_entity_name()} not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_entity = self.update_entity(entity, serializer.validated_data)
            if updated_entity:
                response_serializer = self.get_response_serializer_class()
                if response_serializer:
                    response_data = response_serializer(updated_entity).data
                else:
                    response_data = serializer_class(updated_entity).data
                
                return self.api_response(
                    message=f"{self.get_entity_name()} updated successfully.",
                    data=response_data,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Failed to update {self.get_entity_name()}.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error updating {self.get_entity_name()} {id}: {e}", exc_info=True)
            return self.api_response(
                message=f"Error updating {self.get_entity_name()}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_entity_name(self) -> str:
        """Get the human-readable entity name. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_name()")
    
    def get_entity_by_id(self, entity_id: str):
        """Get entity by ID. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_entity_by_id(entity_id)")
    
    def get_serializer_class(self):
        """Get serializer class for update view. Must be overridden."""
        raise NotImplementedError("Child classes must implement get_serializer_class()")
    
    def update_entity(self, entity: Any, validated_data: dict) -> Optional[Any]:
        """Update the entity. Must be overridden."""
        raise NotImplementedError("Child classes must implement update_entity(entity, validated_data)")
    
    def get_response_serializer_class(self):
        """Get serializer class for response. Override if different from update serializer."""
        return None
