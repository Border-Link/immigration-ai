from django.db import transaction
from django.core.cache import cache
from rules_knowledge.models.visa_type import VisaType


class VisaTypeRepository:
    """Repository for VisaType write operations."""

    @staticmethod
    def create_visa_type(jurisdiction: str, code: str, name: str, description: str = None, is_active: bool = True):
        """Create a new visa type."""
        with transaction.atomic():
            visa_type = VisaType.objects.create(
                jurisdiction=jurisdiction,
                code=code,
                name=name,
                description=description,
                is_active=is_active
            )
            visa_type.full_clean()
            visa_type.save()
            
            # Invalidate cache (try pattern deletion if available, otherwise delete specific keys)
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("visa_type:*")
            except AttributeError:
                pass
            # Delete specific known cache keys
            cache.delete(f"visa_type:{visa_type.id}")
            cache.delete(f"visa_type:{jurisdiction}:{code}")
            
            return visa_type

    @staticmethod
    def update_visa_type(visa_type, **fields):
        """Update visa type fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(visa_type, key):
                    setattr(visa_type, key, value)
            visa_type.full_clean()
            visa_type.save()
            
            # Invalidate cache (try pattern deletion if available, otherwise delete specific keys)
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("visa_type:*")
            except AttributeError:
                pass
            # Delete specific known cache keys
            cache.delete(f"visa_type:{visa_type.id}")
            cache.delete(f"visa_type:{visa_type.jurisdiction}:{visa_type.code}")
            
            return visa_type

    @staticmethod
    def delete_visa_type(visa_type):
        """Delete a visa type."""
        with transaction.atomic():
            # Store values before deletion for cache invalidation
            visa_type_id = visa_type.id
            jurisdiction = visa_type.jurisdiction
            code = visa_type.code
            
            visa_type.delete()
            
            # Invalidate cache (try pattern deletion if available, otherwise delete specific keys)
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("visa_type:*")
            except AttributeError:
                pass
            # Delete specific known cache keys
            cache.delete(f"visa_type:{visa_type_id}")
            cache.delete(f"visa_type:{jurisdiction}:{code}")

