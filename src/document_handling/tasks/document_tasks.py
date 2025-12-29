from celery import shared_task
import logging
from main_system.tasks_base import BaseTaskWithMeta
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def process_document_task(self, document_id: str):
    """
    Celery task to process a document (OCR, classification, validation).
    
    Args:
        document_id: UUID of the document to process
        
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Starting document processing for document: {document_id}")
        
        document = CaseDocumentSelector.get_by_id(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return {'success': False, 'error': 'Document not found'}
        
        # Step 1: OCR Processing (placeholder - implement actual OCR service)
        # For now, we'll just create a check entry
        ocr_check = DocumentCheckService.create_document_check(
            case_document_id=document_id,
            check_type='ocr',
            result='pass',  # Placeholder - implement actual OCR
            details='OCR processing completed'
        )
        
        # Step 2: Classification (placeholder - implement actual classification)
        classification_check = DocumentCheckService.create_document_check(
            case_document_id=document_id,
            check_type='classification',
            result='pass',  # Placeholder - implement actual classification
            details='Document classification completed'
        )
        
        # Step 3: Requirement Matching (placeholder)
        requirement_check = DocumentCheckService.create_document_check(
            case_document_id=document_id,
            check_type='requirement_match',
            result='pass',  # Placeholder - implement actual requirement matching
            details='Requirement matching completed'
        )
        
        # Update document status based on checks
        all_passed = all([
            ocr_check and ocr_check.result == 'pass',
            classification_check and classification_check.result == 'pass',
            requirement_check and requirement_check.result == 'pass'
        ])
        
        if all_passed:
            CaseDocumentService.update_case_document(
                document_id=document_id,
                status='verified'
            )
        else:
            CaseDocumentService.update_case_document(
                document_id=document_id,
                status='needs_attention'
            )
        
        logger.info(f"Document processing completed for document: {document_id}")
        return {
            'success': True,
            'document_id': document_id,
            'ocr_check': str(ocr_check.id) if ocr_check else None,
            'classification_check': str(classification_check.id) if classification_check else None,
            'requirement_check': str(requirement_check.id) if requirement_check else None,
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

