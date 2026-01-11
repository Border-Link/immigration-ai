"""
Service for reprocessing documents (OCR, classification, validation).
"""
import logging
from typing import Optional
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from document_handling.tasks.document_tasks import process_document_task
from document_handling.services.ocr_service import OCRService
from document_handling.services.document_classification_service import DocumentClassificationService
from document_handling.services.document_content_validation_service import DocumentContentValidationService
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService

logger = logging.getLogger('django')


class DocumentReprocessingService:
    """Service for reprocessing documents."""

    @staticmethod
    def reprocess_ocr(case_document_id: str) -> bool:
        """
        Reprocess OCR for a document.
        
        Requires: Case must have a completed payment before document reprocessing.
        
        Args:
            case_document_id: UUID of the case document
            
        Returns:
            True if reprocessing was initiated, False otherwise
        """
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document OCR reprocessing")
            if not is_valid:
                logger.warning(f"Document OCR reprocessing blocked for case {case_document.case.id}: {error}")
                return False
            
            # Run OCR
            ocr_text, ocr_metadata, ocr_error = OCRService.extract_text(
                file_path=case_document.file_path,
                mime_type=case_document.mime_type
            )
            
            ocr_result = 'passed'
            ocr_details = {'metadata': ocr_metadata} if ocr_metadata else {}
            
            if ocr_error or not ocr_text:
                ocr_result = 'failed'
                ocr_details['error'] = ocr_error or 'OCR extracted no text'
            else:
                # Update document with OCR text
                CaseDocumentService.update_case_document(
                    document_id=case_document_id,
                    ocr_text=ocr_text
                )
            
            # Create or update OCR check
            DocumentCheckService.create_document_check(
                case_document_id=case_document_id,
                check_type='ocr',
                result=ocr_result,
                details=ocr_details,
                performed_by='OCR Reprocessing Service'
            )
            
            logger.info(f"OCR reprocessing completed for document {case_document_id}: {ocr_result}")
            return True
            
        except Exception as e:
            logger.error(f"Error reprocessing OCR for document {case_document_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def reprocess_classification(case_document_id: str) -> bool:
        """
        Reprocess classification for a document.
        
        Requires: Case must have a completed payment before document reprocessing.
        
        Args:
            case_document_id: UUID of the case document
            
        Returns:
            True if reprocessing was initiated, False otherwise
        """
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document classification reprocessing")
            if not is_valid:
                logger.warning(f"Document classification reprocessing blocked for case {case_document.case.id}: {error}")
                return False
            
            if not case_document.ocr_text or len(case_document.ocr_text.strip()) < 10:
                logger.warning(f"Insufficient OCR text for classification reprocessing: {case_document_id}")
                return False
            
            # Run classification
            document_type_id, confidence, classification_metadata, classification_error = \
                DocumentClassificationService.classify_document(
                    ocr_text=case_document.ocr_text,
                    file_name=case_document.file_name,
                    file_size=case_document.file_size,
                    mime_type=case_document.mime_type
                )
            
            classification_result = 'passed'
            classification_details = {
                'confidence': confidence,
                'metadata': classification_metadata or {}
            }
            
            if classification_error or not document_type_id:
                classification_result = 'failed'
                classification_details['error'] = classification_error or 'Classification failed'
            else:
                # Update document type if confidence is high enough
                should_auto_classify = DocumentClassificationService.should_auto_classify(confidence)
                
                if should_auto_classify:
                    CaseDocumentService.update_case_document(
                        document_id=case_document_id,
                        document_type_id=document_type_id,
                        classification_confidence=confidence
                    )
                else:
                    classification_result = 'warning'
                    classification_details['requires_review'] = True
                    classification_details['message'] = f"Low confidence ({confidence:.2f}), requires human review"
            
            # Create or update classification check
            DocumentCheckService.create_document_check(
                case_document_id=case_document_id,
                check_type='classification',
                result=classification_result,
                details=classification_details,
                performed_by='Classification Reprocessing Service'
            )
            
            logger.info(f"Classification reprocessing completed for document {case_document_id}: {classification_result}")
            return True
            
        except Exception as e:
            logger.error(f"Error reprocessing classification for document {case_document_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def reprocess_validation(case_document_id: str) -> bool:
        """
        Reprocess content validation for a document.
        
        Requires: Case must have a completed payment before document reprocessing.
        
        Args:
            case_document_id: UUID of the case document
            
        Returns:
            True if reprocessing was initiated, False otherwise
        """
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document validation reprocessing")
            if not is_valid:
                logger.warning(f"Document validation reprocessing blocked for case {case_document.case.id}: {error}")
                return False
            
            if not case_document.ocr_text:
                logger.warning(f"No OCR text available for validation reprocessing: {case_document_id}")
                return False
            
            # Run content validation
            validation_status, validation_details, validation_error = \
                DocumentContentValidationService.validate_content(
                    case_document_id=case_document_id,
                    ocr_text=case_document.ocr_text,
                    extracted_metadata={
                        'expiry_date': case_document.expiry_date.isoformat() if case_document.expiry_date else None,
                        **(case_document.extracted_metadata or {})
                    }
                )
            
            if validation_status and validation_status != 'pending':
                # Update document with validation results
                CaseDocumentService.update_case_document(
                    document_id=case_document_id,
                    content_validation_status=validation_status,
                    content_validation_details=validation_details
                )
                
                # Create or update content validation check
                DocumentCheckService.create_document_check(
                    case_document_id=case_document_id,
                    check_type='content_validation',
                    result=validation_status,
                    details=validation_details or {},
                    performed_by='Content Validation Reprocessing Service'
                )
            
            logger.info(f"Validation reprocessing completed for document {case_document_id}: {validation_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error reprocessing validation for document {case_document_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def reprocess_full(case_document_id: str) -> bool:
        """
        Trigger full reprocessing of a document (async).
        
        Requires: Case must have a completed payment before document reprocessing.
        
        Args:
            case_document_id: UUID of the case document
            
        Returns:
            True if reprocessing was initiated, False otherwise
        """
        from payments.helpers.payment_validator import PaymentValidator
        
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                logger.error(f"Case document {case_document_id} not found")
                return False
            
            # Validate payment requirement
            is_valid, error = PaymentValidator.validate_case_has_payment(case_document.case, operation_name="document full reprocessing")
            if not is_valid:
                logger.warning(f"Document full reprocessing blocked for case {case_document.case.id}: {error}")
                return False
            
            # Trigger async full reprocessing
            process_document_task.delay(case_document_id)
            
            logger.info(f"Full reprocessing initiated for document {case_document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initiating full reprocessing for document {case_document_id}: {e}", exc_info=True)
            return False
