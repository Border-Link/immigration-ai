import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from document_handling.models.case_document import CaseDocument
from document_handling.repositories.case_document_repository import CaseDocumentRepository
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from immigration_cases.selectors.case_selector import CaseSelector
from immigration_cases.models.case import Case
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "case_documents"


class CaseDocumentService:
    """Service for CaseDocument business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda doc: doc is not None)
    def create_case_document(case_id: str, document_type_id: str, file_path: str,
                            file_name: str, file_size: int = None, mime_type: str = None,
                            status: str = 'uploaded'):
        """
        Create a new case document.
        
        Requires: Case must have a completed payment before documents can be uploaded.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            # Get case
            case = CaseSelector.get_by_id(case_id)
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="document upload")
            if not is_valid:
                logger.warning(f"Document upload blocked for case {case_id}: {error}")
                raise ValidationError(error)
            
            # Get document type
            document_type = DocumentTypeSelector.get_by_id(document_type_id)
            if not document_type.is_active:
                logger.error(f"Document type {document_type_id} is not active")
                return None
            
            return CaseDocumentRepository.create_case_document(
                case=case,
                document_type=document_type,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                status=status
            )
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error creating case document: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")  # 5 minutes - document list changes frequently
    def get_all():
        """Get all case documents."""
        try:
            return CaseDocumentSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all case documents: {e}")
            return CaseDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache documents by case
    def get_by_case(case_id: str):
        """Get documents by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return CaseDocumentSelector.get_by_case(case)
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return CaseDocumentSelector.get_none()
        except Exception as e:
            logger.error(f"Error fetching documents for case {case_id}: {e}")
            return CaseDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['status'], namespace=namespace, user_scope="global")  # 5 minutes - cache documents by status
    def get_by_status(status: str):
        """Get documents by status."""
        try:
            return CaseDocumentSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching documents by status {status}: {e}")
            return CaseDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['document_type_id'], namespace=namespace, user_scope="global")  # 5 minutes - cache documents by type
    def get_by_document_type(document_type_id: str):
        """Get documents by document type."""
        try:
            return CaseDocumentSelector.get_by_document_type(document_type_id)
        except Exception as e:
            logger.error(f"Error fetching documents by document type {document_type_id}: {e}")
            return CaseDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['document_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache document by ID
    def get_by_id(document_id: str) -> Optional[CaseDocument]:
        """Get case document by ID."""
        try:
            return CaseDocumentSelector.get_by_id(document_id)
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {document_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching case document {document_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda doc: doc is not None)
    def update_case_document(document_id: str, **fields) -> Optional[CaseDocument]:
        """
        Update case document.
        
        Requires: Case must have a completed payment before documents can be updated.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(document_id)
            if not case_document:
                logger.error(f"Case document {document_id} not found")
                return None
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document update")
            if not is_valid:
                logger.warning(f"Document update blocked for case {case_document.case.id}: {error}")
                raise ValidationError(error)
            
            # Handle document_type_id separately (convert to ForeignKey)
            if 'document_type_id' in fields:
                from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector
                document_type_id = fields.pop('document_type_id')
                document_type = DocumentTypeSelector.get_by_id(document_type_id)
                if document_type:
                    fields['document_type'] = document_type
                else:
                    logger.warning(f"Document type {document_type_id} not found, skipping update")
            
            return CaseDocumentRepository.update_case_document(case_document, **fields)
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {document_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating case document {document_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda doc: doc is not None)
    def update_status(document_id: str, status: str) -> Optional[CaseDocument]:
        """
        Update document status.
        
        Requires: Case must have a completed payment before document status can be updated.
        Note: Internal status updates during processing may bypass this if payment was already validated,
        but user-initiated status updates require payment.
        """
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(document_id)
            if not case_document:
                logger.error(f"Case document {document_id} not found")
                return None
            
            # Validate payment requirement (uses cache, so fast even if called multiple times)
            # This provides defense in depth even for internal status updates
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document status update")
            if not is_valid:
                logger.warning(f"Document status update blocked for case {case_document.case.id}: {error}")
                # For internal processing, we might want to allow status updates to 'rejected' or 'failed'
                # But for user-initiated updates, we should block
                # For now, we block all status updates without payment for consistency
                return None
            
            return CaseDocumentRepository.update_status(case_document, status)
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {document_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating document status {document_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_case_document(document_id: str) -> bool:
        """
        Delete case document and its stored file.
        
        Requires: Case must have a completed payment before documents can be deleted.
        This prevents abuse and ensures only paid cases can manage their documents.
        """
        from django.core.exceptions import ValidationError
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(document_id)
            if not case_document:
                logger.error(f"Case document {document_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document deletion")
            if not is_valid:
                logger.warning(f"Document deletion blocked for case {case_document.case.id}: {error}")
                raise ValidationError(error)
            
            # Delete the stored file
            if case_document.file_path:
                from document_handling.services.file_storage_service import FileStorageService
                FileStorageService.delete_file(case_document.file_path)
            
            # Delete the database record
            CaseDocumentRepository.delete_case_document(case_document)
            return True
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {document_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting case document {document_id}: {e}")
            return False
    
    @staticmethod
    def get_file_url(document_id: str) -> Optional[str]:
        """Get URL to access the document file."""
        try:
            case_document = CaseDocumentSelector.get_by_id(document_id)
            if not case_document or not case_document.file_path:
                return None
            
            from document_handling.services.file_storage_service import FileStorageService
            return FileStorageService.get_file_url(case_document.file_path)
        except Exception as e:
            logger.error(f"Error getting file URL for document {document_id}: {e}")
            return None

    @staticmethod
    def get_verified_by_case(case_id: str):
        """Get verified documents by case."""
        try:
            case = CaseSelector.get_by_id(case_id)
            return CaseDocumentSelector.get_verified_by_case(case)
        except Case.DoesNotExist:
            logger.error(f"Case {case_id} not found")
            return CaseDocumentSelector.get_none()
        except Exception as e:
            logger.error(f"Error fetching verified documents for case {case_id}: {e}")
            return CaseDocumentSelector.get_none()

    @staticmethod
    def get_by_filters(case_id: str = None, document_type_id: str = None, status: str = None,
                       has_ocr_text: bool = None, min_confidence: float = None,
                       date_from=None, date_to=None, mime_type: str = None,
                       has_expiry_date: bool = None, expiry_date_from=None, expiry_date_to=None,
                       content_validation_status: str = None, is_expired: bool = None):
        """Get case documents with filters."""
        try:
            return CaseDocumentSelector.get_by_filters(
                case_id=case_id,
                document_type_id=document_type_id,
                status=status,
                has_ocr_text=has_ocr_text,
                min_confidence=min_confidence,
                date_from=date_from,
                date_to=date_to,
                mime_type=mime_type,
                has_expiry_date=has_expiry_date,
                expiry_date_from=expiry_date_from,
                expiry_date_to=expiry_date_to,
                content_validation_status=content_validation_status,
                is_expired=is_expired
            )
        except Exception as e:
            logger.error(f"Error fetching filtered case documents: {e}")
            return CaseDocumentSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get case document statistics."""
        try:
            return CaseDocumentSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting case document statistics: {e}")
            return {}

