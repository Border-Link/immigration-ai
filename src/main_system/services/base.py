"""
Base Service Mixin

Common patterns for service methods.
"""
import logging
from typing import Optional, Type, Any
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger('django')


class BaseServiceMixin:
    """
    Base mixin for service classes.
    
    Provides common get_by_id pattern with:
    - Error handling (DoesNotExist, ValueError, Exception)
    - Logging
    - Consistent return type (Optional[Model])
    
    Usage:
        class MyService(BaseServiceMixin):
            @staticmethod
            @cache_result(timeout=600, keys=['my_id'])
            def get_by_id(my_id: str) -> Optional[MyModel]:
                return BaseServiceMixin._get_by_id(
                    selector=MySelector,
                    model_class=MyModel,
                    entity_id=my_id,
                    entity_name="MyModel"
                )
    """
    
    @staticmethod
    def _get_by_id(
        selector: Any,
        model_class: Type,
        entity_id: str,
        entity_name: str = "Entity"
    ) -> Optional[Any]:
        """
        Common get_by_id implementation.
        
        Args:
            selector: Selector class with get_by_id method
            model_class: Model class for DoesNotExist exception
            entity_id: ID of entity to fetch
            entity_name: Human-readable name for logging
            
        Returns:
            Model instance or None if not found/error
        """
        try:
            return selector.get_by_id(entity_id)
        except model_class.DoesNotExist:
            logger.warning(f"{entity_name} {entity_id} not found")
            return None
        except ValueError as e:
            logger.error(f"Invalid {entity_name} ID format '{entity_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {entity_name} {entity_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _activate_model(
        service: Any,
        model_class: Type,
        entity_id: str,
        is_active: bool,
        entity_name: str = "Entity",
        activate_method_name: str = "activate"
    ) -> Optional[Any]:
        """
        Common activate/deactivate implementation.
        
        Args:
            service: Service instance with activate method
            model_class: Model class for DoesNotExist exception
            entity_id: ID of entity to activate/deactivate
            is_active: True to activate, False to deactivate
            entity_name: Human-readable name for logging
            activate_method_name: Name of activate method on service
            
        Returns:
            Updated model instance or None if not found/error
        """
        try:
            # Get entity
            entity = service.get_by_id(entity_id)
            if not entity:
                logger.warning(f"{entity_name} {entity_id} not found")
                return None
            
            # Activate/deactivate
            activate_method = getattr(service, activate_method_name)
            if hasattr(entity, 'is_active'):
                # Direct field update
                updated = activate_method(entity, is_active)
            else:
                # Method-based activation
                updated = activate_method(entity_id, is_active)
            
            return updated
        except model_class.DoesNotExist:
            logger.warning(f"{entity_name} {entity_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error activating/deactivating {entity_name} {entity_id}: {e}", exc_info=True)
            return None
