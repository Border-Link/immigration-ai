from django.db import transaction
from django.core.cache import cache
from rules_knowledge.models.document_type import DocumentType


class DocumentTypeRepository:
    """Repository for DocumentType write operations."""

    @staticmethod
    def create_document_type(code: str, name: str, description: str = None, is_active: bool = True):
        """Create a new document type."""
        with transaction.atomic():
            document_type = DocumentType.objects.create(
                code=code,
                name=name,
                description=description,
                is_active=is_active
            )
            document_type.full_clean()
            document_type.save()
            
            # Invalidate cache (try pattern deletion if available, otherwise delete specific keys)
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("document_type:*")
            except AttributeError:
                pass
            # Delete specific known cache keys
            cache.delete(f"document_type:{document_type.id}")
            cache.delete(f"document_type:code:{code}")
            
            return document_type

    @staticmethod
    def update_document_type(document_type, **fields):
        """Update document type fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(document_type, key):
                    setattr(document_type, key, value)
            document_type.full_clean()
            document_type.save()
            
            # Invalidate cache
            cache.delete_pattern("document_type:*")
            cache.delete(f"document_type:{document_type.id}")
            cache.delete(f"document_type:code:{document_type.code}")
            
            return document_type

    @staticmethod
    def delete_document_type(document_type):
        """Delete a document type."""
        with transaction.atomic():
            # Store values before deletion for cache invalidation
            document_type_id = document_type.id
            code = document_type.code
            
            document_type.delete()
            
            # Invalidate cache
            cache.delete_pattern("document_type:*")
            cache.delete(f"document_type:{document_type_id}")
            cache.delete(f"document_type:code:{code}")

