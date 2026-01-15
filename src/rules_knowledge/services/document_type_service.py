import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from rules_knowledge.models.document_type import DocumentType
from rules_knowledge.repositories.document_type_repository import DocumentTypeRepository
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "document_types"


class DocumentTypeService:
    """Service for DocumentType business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda dt: dt is not None)
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
            
            document_type = DocumentTypeRepository.create_document_type(code, name, description, is_active)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Document type created: {code} ({name})",
                    func_name='create_document_type',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return document_type
        except Exception as e:
            logger.error(f"Error creating document type {code}: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=1800, keys=[], namespace=namespace, user_scope="global")  # 30 minutes - rarely changes
    def get_all():
        """Get all document types."""
        try:
            return DocumentTypeSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document types: {e}")
            return DocumentType.objects.none()

    @staticmethod
    @cache_result(timeout=1800, keys=[], namespace=namespace, user_scope="global")  # 30 minutes - rarely changes
    def get_active():
        """Get all active document types."""
        try:
            return DocumentTypeSelector.get_active()
        except Exception as e:
            logger.error(f"Error fetching active document types: {e}")
            return DocumentType.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['code'], namespace=namespace, user_scope="global")  # 1 hour - cache by code
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
    @cache_result(timeout=3600, keys=['type_id'], namespace=namespace, user_scope="global")  # 1 hour - cache by ID
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
    @invalidate_cache(namespace, predicate=lambda dt: dt is not None)
    def update_document_type(type_id: str, **fields) -> Optional[DocumentType]:
        """Update document type."""
        try:
            document_type = DocumentTypeSelector.get_by_id(type_id)
            updated_document_type = DocumentTypeRepository.update_document_type(document_type, **fields)
            
            # Log audit event
            try:
                changes = ', '.join([f"{k}={v}" for k, v in fields.items()])
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Document type {type_id} updated: {changes}",
                    func_name='update_document_type',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_document_type
        except DocumentType.DoesNotExist:
            logger.error(f"Document type {type_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating document type {type_id}: {e}", exc_info=True)
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_document_type(type_id: str) -> bool:
        """Delete document type."""
        try:
            document_type = DocumentTypeSelector.get_by_id(type_id)
            DocumentTypeRepository.delete_document_type(document_type)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='rules_knowledge',
                    message=f"Document type {type_id} deleted: {document_type.code} ({document_type.name})",
                    func_name='delete_document_type',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except DocumentType.DoesNotExist:
            logger.error(f"Document type {type_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document type {type_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def get_by_filters(is_active=None, code=None, date_from=None, date_to=None):
        """Get document types with advanced filtering for admin."""
        try:
            return DocumentTypeSelector.get_by_filters(
                is_active=is_active,
                code=code,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering document types: {e}")
            return DocumentType.objects.none()

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda dt: dt is not None)
    def activate_document_type(document_type, is_active: bool) -> Optional[DocumentType]:
        """Activate or deactivate a document type."""
        try:
            return DocumentTypeRepository.update_document_type(document_type, is_active=is_active)
        except Exception as e:
            logger.error(f"Error activating/deactivating document type: {e}")
            return None
