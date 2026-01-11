from celery import shared_task
import logging
import time
from main_system.utils.tasks_base import BaseTaskWithMeta
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService
from document_handling.services.ocr_service import OCRService
from document_handling.services.document_classification_service import DocumentClassificationService
from document_handling.services.document_expiry_extraction_service import DocumentExpiryExtractionService
from document_handling.services.document_content_validation_service import DocumentContentValidationService
from document_handling.services.document_requirement_matching_service import DocumentRequirementMatchingService
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.services.processing_history_service import ProcessingHistoryService

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def process_document_task(self, document_id: str):
    """
    Celery task to process a document (OCR, classification, validation).
    
    This implements the workflow from implementation.md Section 8:
    1. OCR Extraction → Store text
    2. AI Classification → Update document_type_id
    3. Requirement Matching → Validate against visa requirements
    
    Args:
        document_id: UUID of the document to process
        
    Returns:
        Dict with processing results
    """
    processing_job = None
    processing_start_time = time.time()
    
    try:
        logger.info(f"Starting document processing for document: {document_id}")
        
        # Create processing job
        processing_job = ProcessingJobService.create_processing_job(
            case_document_id=document_id,
            processing_type='full',
            celery_task_id=self.request.id,
            metadata={'task_name': 'process_document_task'}
        )
        
        if processing_job:
            # Log job started
            ProcessingHistoryService.create_history_entry(
                case_document_id=document_id,
                processing_job_id=str(processing_job.id),
                action='job_started',
                status='success',
                message='Document processing started'
            )
            logger.info(f"Created processing job {processing_job.id} for document {document_id}")
        
        # Update status to processing
        CaseDocumentService.update_case_document(
            document_id=document_id,
            status='processing'
        )
        
        document = CaseDocumentSelector.get_by_id(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            if processing_job:
                ProcessingJobService.update_status(str(processing_job.id), 'failed')
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='job_failed',
                    status='failure',
                    error_type='DocumentNotFound',
                    error_message='Document not found'
                )
            return {'success': False, 'error': 'Document not found'}
        
        # Step 1: OCR Processing
        logger.info(f"Step 1: Running OCR for document {document_id}")
        
        if processing_job:
            ProcessingHistoryService.create_history_entry(
                case_document_id=document_id,
                processing_job_id=str(processing_job.id),
                action='ocr_started',
                status='success',
                message='OCR processing started'
            )
        ocr_text, ocr_metadata, ocr_error = OCRService.extract_text(
            file_path=document.file_path,
            mime_type=document.mime_type
        )
        
        ocr_start_time = time.time()
        ocr_result = 'passed'
        ocr_details = {'metadata': ocr_metadata} if ocr_metadata else {}
        
        if ocr_error or not ocr_text:
            ocr_result = 'failed'
            ocr_details['error'] = ocr_error or 'OCR extracted no text'
            logger.warning(f"OCR failed for document {document_id}: {ocr_error}")
            
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='ocr_failed',
                    status='failure',
                    error_type='OCRError',
                    error_message=ocr_error or 'OCR extracted no text',
                    processing_time_ms=int((time.time() - ocr_start_time) * 1000)
                )
        else:
            # Store OCR text in document
            CaseDocumentService.update_case_document(
                document_id=document_id,
                ocr_text=ocr_text
            )
            logger.info(f"OCR successful: {len(ocr_text)} characters extracted")
            
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='ocr_completed',
                    status='success',
                    message=f'OCR completed: {len(ocr_text)} characters extracted',
                    processing_time_ms=int((time.time() - ocr_start_time) * 1000),
                    metadata={'text_length': len(ocr_text), 'metadata': ocr_metadata}
                )
        
        # Create OCR check
        ocr_check = DocumentCheckService.create_document_check(
            case_document_id=document_id,
            check_type='ocr',
            result=ocr_result,
            details=ocr_details,
            performed_by='OCR Service'
        )
        
        # Step 2: Document Classification (only if OCR succeeded)
        classification_check = None
        if ocr_text and len(ocr_text.strip()) > 10:
            logger.info(f"Step 2: Classifying document {document_id}")
            
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='classification_started',
                    status='success',
                    message='Document classification started'
                )
            
            classification_start_time = time.time()
            document_type_id, confidence, classification_metadata, classification_error = \
                DocumentClassificationService.classify_document(
                    ocr_text=ocr_text,
                    file_name=document.file_name,
                    file_size=document.file_size,
                    mime_type=document.mime_type
                )
            
            classification_result = 'passed'
            classification_details = {
                'confidence': confidence,
                'metadata': classification_metadata or {}
            }
            
            if classification_error or not document_type_id:
                classification_result = 'failed'
                classification_details['error'] = classification_error or 'Classification failed'
                logger.warning(f"Classification failed for document {document_id}: {classification_error}")
                
                if processing_job:
                    ProcessingHistoryService.create_history_entry(
                        case_document_id=document_id,
                        processing_job_id=str(processing_job.id),
                        action='classification_failed',
                        status='failure',
                        error_type='ClassificationError',
                        error_message=classification_error or 'Classification failed',
                        processing_time_ms=int((time.time() - classification_start_time) * 1000)
                    )
            else:
                # Update document type if confidence is high enough
                should_auto_classify = DocumentClassificationService.should_auto_classify(confidence)
                
                if should_auto_classify:
                    # Auto-update document type
                    CaseDocumentService.update_case_document(
                        document_id=document_id,
                        document_type_id=document_type_id,
                        classification_confidence=confidence
                    )
                    logger.info(
                        f"Document type auto-updated to {document_type_id} "
                        f"(confidence: {confidence:.2f})"
                    )
                    
                    if processing_job:
                        ProcessingHistoryService.create_history_entry(
                            case_document_id=document_id,
                            processing_job_id=str(processing_job.id),
                            action='classification_completed',
                            status='success',
                            message=f'Classification completed: {document_type_id} (confidence: {confidence:.2f})',
                            processing_time_ms=int((time.time() - classification_start_time) * 1000),
                            metadata={'document_type_id': str(document_type_id), 'confidence': confidence}
                        )
                else:
                    # Low confidence - flag for human review
                    classification_result = 'warning'
                    classification_details['requires_review'] = True
                    classification_details['message'] = f"Low confidence ({confidence:.2f}), requires human review"
                    logger.info(
                        f"Classification confidence too low ({confidence:.2f}), "
                        f"flagging for human review"
                    )
                    
                    if processing_job:
                        ProcessingHistoryService.create_history_entry(
                            case_document_id=document_id,
                            processing_job_id=str(processing_job.id),
                            action='classification_completed',
                            status='warning',
                            message=f'Classification completed with low confidence ({confidence:.2f}), requires review',
                            processing_time_ms=int((time.time() - classification_start_time) * 1000),
                            metadata={'document_type_id': str(document_type_id) if document_type_id else None, 'confidence': confidence}
                        )
            
            # Create classification check
            classification_check = DocumentCheckService.create_document_check(
                case_document_id=document_id,
                check_type='classification',
                result=classification_result,
                details=classification_details,
                performed_by='AI Classification Service'
            )
        else:
            logger.warning(f"Skipping classification for document {document_id}: insufficient OCR text")
            classification_check = DocumentCheckService.create_document_check(
                case_document_id=document_id,
                check_type='classification',
                result='pending',
                details={'reason': 'Insufficient OCR text for classification'},
                performed_by='AI Classification Service'
            )
        
        # Step 3: Expiry Date Extraction (if document type supports it)
        expiry_date = None
        expiry_confidence = None
        expiry_metadata = None
        
        if document.document_type and document.document_type.code in ['passport', 'visa', 'certificate', 'license']:
            logger.info(f"Step 3: Extracting expiry date for document {document_id}")
            
            expiry_start_time = time.time()
            expiry_date, expiry_confidence, expiry_metadata, expiry_error = \
                DocumentExpiryExtractionService.extract_expiry_date(
                    ocr_text=ocr_text,
                    document_type_code=document.document_type.code if document.document_type else None,
                    file_name=document.file_name
                )
            
            if expiry_date:
                # Update document with expiry date
                CaseDocumentService.update_case_document(
                    document_id=document_id,
                    expiry_date=expiry_date
                )
                logger.info(f"Expiry date extracted: {expiry_date}")
                
                if processing_job:
                    ProcessingHistoryService.create_history_entry(
                        case_document_id=document_id,
                        processing_job_id=str(processing_job.id),
                        action='validation_completed',
                        status='success',
                        message=f'Expiry date extracted: {expiry_date}',
                        processing_time_ms=int((time.time() - expiry_start_time) * 1000),
                        metadata={'expiry_date': expiry_date.isoformat(), 'confidence': expiry_confidence}
                    )
            elif expiry_error:
                logger.warning(f"Expiry date extraction failed: {expiry_error}")
                
                if processing_job:
                    ProcessingHistoryService.create_history_entry(
                        case_document_id=document_id,
                        processing_job_id=str(processing_job.id),
                        action='validation_failed',
                        status='warning',
                        error_type='ExpiryExtractionError',
                        error_message=expiry_error,
                        processing_time_ms=int((time.time() - expiry_start_time) * 1000)
                    )
        
        # Step 4: Content Validation against Case Facts
        logger.info(f"Step 4: Validating content against case facts for document {document_id}")
        
        if processing_job:
            ProcessingHistoryService.create_history_entry(
                case_document_id=document_id,
                processing_job_id=str(processing_job.id),
                action='validation_started',
                status='success',
                message='Content validation started'
            )
        
        validation_start_time = time.time()
        validation_status, validation_details, validation_error = \
            DocumentContentValidationService.validate_content(
                case_document_id=document_id,
                ocr_text=ocr_text,
                extracted_metadata={
                    'expiry_date': expiry_date.isoformat() if expiry_date else None,
                    'expiry_confidence': expiry_confidence,
                    **(expiry_metadata or {})
                }
            )
        
        if validation_status and validation_status != 'pending':
            # Update document with validation results
            CaseDocumentService.update_case_document(
                document_id=document_id,
                content_validation_status=validation_status,
                content_validation_details=validation_details,
                extracted_metadata={
                    'expiry_date': expiry_date.isoformat() if expiry_date else None,
                    'expiry_confidence': expiry_confidence,
                    **(expiry_metadata or {}),
                    **(validation_details or {})
                }
            )
            
            # Create content validation check
            DocumentCheckService.create_document_check(
                case_document_id=document_id,
                check_type='content_validation',
                result=validation_status,
                details=validation_details or {},
                performed_by='Content Validation Service'
            )
            logger.info(f"Content validation completed: {validation_status}")
            
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='validation_completed',
                    status='success' if validation_status == 'passed' else 'warning',
                    message=f'Content validation completed: {validation_status}',
                    processing_time_ms=int((time.time() - validation_start_time) * 1000),
                    metadata={'validation_status': validation_status, 'details': validation_details}
                )
        elif validation_error:
            logger.warning(f"Content validation failed: {validation_error}")
            
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='validation_failed',
                    status='failure',
                    error_type='ValidationError',
                    error_message=validation_error,
                    processing_time_ms=int((time.time() - validation_start_time) * 1000)
                )
        
        # Step 5: Requirement Matching
        logger.info(f"Step 5: Matching document against visa requirements for document {document_id}")
        
        if processing_job:
            ProcessingHistoryService.create_history_entry(
                case_document_id=document_id,
                processing_job_id=str(processing_job.id),
                action='validation_started',
                status='success',
                message='Requirement matching started'
            )
        
        requirement_start_time = time.time()
        requirement_result, requirement_details, requirement_error = \
            DocumentRequirementMatchingService.match_document_against_requirements(document_id)
        
        if requirement_error:
            logger.warning(f"Requirement matching failed: {requirement_error}")
            requirement_result = 'failed'
            requirement_details['error'] = requirement_error
            
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='validation_failed',
                    status='failure',
                    error_type='RequirementMatchingError',
                    error_message=requirement_error,
                    processing_time_ms=int((time.time() - requirement_start_time) * 1000)
                )
        else:
            if processing_job:
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='validation_completed',
                    status='success' if requirement_result == 'passed' else 'warning',
                    message=f'Requirement matching completed: {requirement_result}',
                    processing_time_ms=int((time.time() - requirement_start_time) * 1000),
                    metadata={'requirement_result': requirement_result, 'details': requirement_details}
                )
        
        requirement_check = DocumentCheckService.create_document_check(
            case_document_id=document_id,
            check_type='requirement_match',
            result=requirement_result,
            details=requirement_details,
            performed_by='Requirement Matching Service'
        )
        
        # Step 6: Update document status based on checks
        # Status = 'verified' if all critical checks pass
        # Status = 'rejected' if any critical check fails
        # Status = 'needs_attention' if warnings or pending checks
        
        # Get content validation check if it exists
        from document_handling.selectors.document_check_selector import DocumentCheckSelector
        content_validation_checks = DocumentCheckSelector.get_by_filters(
            case_document_id=document_id,
            check_type='content_validation'
        )
        content_validation_check = content_validation_checks.first() if content_validation_checks.exists() else None
        
        critical_checks_passed = (
            ocr_check and ocr_check.result == 'passed' and
            classification_check and classification_check.result in ['passed', 'warning']
        )
        
        has_failures = (
            (ocr_check and ocr_check.result == 'failed') or
            (classification_check and classification_check.result == 'failed') or
            (content_validation_check and content_validation_check.result == 'failed')
        )
        
        if has_failures:
            final_status = 'rejected'
        elif critical_checks_passed:
            final_status = 'verified'
        else:
            final_status = 'needs_attention'
        
        CaseDocumentService.update_case_document(
            document_id=document_id,
            status=final_status
        )
        
        # Update processing job status to completed
        if processing_job:
            ProcessingJobService.update_status(str(processing_job.id), 'completed')
            ProcessingHistoryService.create_history_entry(
                case_document_id=document_id,
                processing_job_id=str(processing_job.id),
                action='job_completed',
                status='success',
                message=f'Document processing completed successfully: {final_status}',
                processing_time_ms=int((time.time() - processing_start_time) * 1000),
                metadata={
                    'final_status': final_status,
                    'ocr_result': ocr_result,
                    'classification_result': classification_check.result if classification_check else None,
                    'content_validation_status': validation_status
                }
            )
        
        logger.info(
            f"Document processing completed for document {document_id}: "
            f"status={final_status}, ocr={ocr_result}, classification={classification_check.result if classification_check else 'N/A'}, "
            f"expiry_date={expiry_date}, content_validation={validation_status}"
        )
        
        return {
            'success': True,
            'document_id': document_id,
            'processing_job_id': str(processing_job.id) if processing_job else None,
            'status': final_status,
            'ocr_check': str(ocr_check.id) if ocr_check else None,
            'classification_check': str(classification_check.id) if classification_check else None,
            'content_validation_check': str(content_validation_check.id) if content_validation_check else None,
            'requirement_check': str(requirement_check.id) if requirement_check else None,
            'ocr_text_length': len(ocr_text) if ocr_text else 0,
            'classification_confidence': classification_check.details.get('confidence') if classification_check and classification_check.details else None,
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
            'content_validation_status': validation_status
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        
        # Update processing job status to failed
        if processing_job:
            try:
                ProcessingJobService.update_status(str(processing_job.id), 'failed')
                ProcessingJobService.update_processing_job(
                    str(processing_job.id),
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                ProcessingHistoryService.create_history_entry(
                    case_document_id=document_id,
                    processing_job_id=str(processing_job.id),
                    action='job_failed',
                    status='failure',
                    error_type=type(e).__name__,
                    error_message=str(e),
                    processing_time_ms=int((time.time() - processing_start_time) * 1000)
                )
            except Exception as history_error:
                logger.error(f"Error updating processing job history: {history_error}")
        
        # Update status to indicate failure
        try:
            CaseDocumentService.update_case_document(
                document_id=document_id,
                status='needs_attention'
            )
        except:
            pass
        raise self.retry(exc=e, countdown=60, max_retries=3)

