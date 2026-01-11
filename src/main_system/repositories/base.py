"""
Base Repository Mixin

Common patterns for repository update methods.
"""
from django.db import transaction
from django.core.cache import cache
from typing import Any, Dict, Optional


class BaseRepositoryMixin:
    """
    Base mixin for repository classes.
    
    Provides common update pattern:
    - Transaction wrapping
    - Field iteration and setting
    - full_clean() and save()
    - Optional cache invalidation
    
    Usage:
        class MyRepository(BaseRepositoryMixin):
            @staticmethod
            def update_my_model(model_instance, **fields):
                return BaseRepositoryMixin.update_model_fields(
                    model_instance,
                    **fields,
                    cache_keys=['my_model:{model_instance.id}']
                )
    """
    
    @staticmethod
    def update_model_fields(
        model_instance: Any,
        cache_keys: Optional[list] = None,
        exclude_fields: Optional[list] = None,
        **fields: Dict[str, Any]
    ) -> Any:
        """
        Update model fields with common pattern.
        
        Args:
            model_instance: Django model instance to update
            **fields: Fields to update
            cache_keys: Optional list of cache keys to invalidate
            exclude_fields: Optional list of field names to exclude from update
            
        Returns:
            Updated model instance
        """
        exclude_fields = exclude_fields or []
        
        with transaction.atomic():
            # Update fields
            for key, value in fields.items():
                if hasattr(model_instance, key) and key not in exclude_fields:
                    setattr(model_instance, key, value)
            
            # Validate and save
            model_instance.full_clean()
            model_instance.save()
            
            # Invalidate cache if keys provided
            if cache_keys:
                for cache_key in cache_keys:
                    cache.delete(cache_key)
            
            return model_instance
