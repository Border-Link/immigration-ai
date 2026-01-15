from django.db import transaction
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
            return document_type

    @staticmethod
    def delete_document_type(document_type):
        """Delete a document type."""
        with transaction.atomic():
            # Store values before deletion for cache invalidation
            document_type_id = document_type.id
            code = document_type.code
            
            document_type.delete()

