import logging
from typing import Optional
from rules_knowledge.models.document_type import DocumentType
from rules_knowledge.repositories.document_type_repository import DocumentTypeRepository
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector

logger = logging.getLogger('django')


class DocumentTypeService:
    """Service for DocumentType business logic."""

    @staticmethod
    def create_document_type(code: str, name: str, description: str = None, is_active: bool = True):
        """Create a new document type."""
        try:
            # Check if code already exists
            try:
                DocumentTypeSelector.get_by_code(code)
                logger.warning(f"Document type with code {code} already exists")
                return None
            except DocumentType.DoesNotExist:
                pass
            
            return DocumentTypeRepository.create_document_type(code, name, description, is_active)
        except Exception as e:
            logger.error(f"Error creating document type {code}: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all document types."""
        try:
            return DocumentTypeSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document types: {e}")
            return DocumentType.objects.none()

    @staticmethod
    def get_active():
        """Get all active document types."""
        try:
            return DocumentTypeSelector.get_active()
        except Exception as e:
            logger.error(f"Error fetching active document types: {e}")
            return DocumentType.objects.none()

    @staticmethod
    def get_by_code(code: str) -> Optional[DocumentType]:
        """Get document type by code."""
        try:
            return DocumentTypeSelector.get_by_code(code)
        except DocumentType.DoesNotExist:
            logger.error(f"Document type with code {code} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document type {code}: {e}")
            return None

    @staticmethod
    def get_by_id(type_id: str) -> Optional[DocumentType]:
        """Get document type by ID."""
        try:
            return DocumentTypeSelector.get_by_id(type_id)
        except DocumentType.DoesNotExist:
            logger.error(f"Document type {type_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document type {type_id}: {e}")
            return None

    @staticmethod
    def update_document_type(type_id: str, **fields) -> Optional[DocumentType]:
        """Update document type."""
        try:
            document_type = DocumentTypeSelector.get_by_id(type_id)
            return DocumentTypeRepository.update_document_type(document_type, **fields)
        except DocumentType.DoesNotExist:
            logger.error(f"Document type {type_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating document type {type_id}: {e}")
            return None

    @staticmethod
    def delete_document_type(type_id: str) -> bool:
        """Delete document type."""
        try:
            document_type = DocumentTypeSelector.get_by_id(type_id)
            DocumentTypeRepository.delete_document_type(document_type)
            return True
        except DocumentType.DoesNotExist:
            logger.error(f"Document type {type_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document type {type_id}: {e}")
            return False

