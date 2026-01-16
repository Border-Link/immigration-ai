"""
Document Classification Service

Service for classifying document types using AI/LLM.
Uses OCR text and file metadata to predict document type.
"""
import logging
from typing import Tuple, Optional, Dict
from django.conf import settings
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector
from document_handling.helpers.prompts import (
    build_document_classification_prompt,
    get_classification_system_message
)
from document_handling.helpers.llm_helper import (
    call_llm_for_document_processing,
    parse_llm_json_response
)
from data_ingestion.exceptions.rule_parsing_exceptions import (
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceUnavailableError,
    LLMAPIKeyError,
    LLMInvalidResponseError
)

logger = logging.getLogger('django')


class DocumentClassificationService:
    """
    Service for classifying document types using AI.
    Uses LLM to analyze OCR text and metadata to predict document type.
    """

    # Minimum confidence threshold for auto-classification
    CONFIDENCE_THRESHOLD = 0.7

    @staticmethod
    def classify_document(
        ocr_text: str,
        file_name: str = None,
        file_size: int = None,
        mime_type: str = None
    ) -> Tuple[Optional[str], Optional[float], Optional[Dict], Optional[str]]:
        """
        Classify document type using AI.
        
        Args:
            ocr_text: Extracted text from OCR
            file_name: Original file name
            file_size: File size in bytes
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (document_type_code, confidence_score, metadata, error_message)
            - document_type_code: Predicted document type code (e.g., 'passport', 'bank_statement')
            - confidence_score: Confidence score (0.0 to 1.0)
            - metadata: Additional classification metadata
            - error_message: Error message if classification failed
        """
        try:
            # Get available document types
            document_types = DocumentTypeSelector.get_all_active()
            if not document_types.exists():
                return None, None, None, "No active document types found"
            
            # Build list of possible document types
            possible_types = [dt.code for dt in document_types]
            
            # Use LLM for classification
            classification_result = DocumentClassificationService._classify_with_llm(
                ocr_text=ocr_text,
                file_name=file_name,
                possible_types=possible_types
            )
            
            if not classification_result:
                return None, None, None, "LLM classification failed"
            
            document_type_code = classification_result.get('document_type')
            confidence = classification_result.get('confidence', 0.0)
            metadata = classification_result.get('metadata', {})
            
            # Validate document type exists
            document_type = document_types.filter(code=document_type_code).first()
            if not document_type:
                logger.warning(f"LLM returned unknown document type: {document_type_code}")
                return None, confidence, metadata, f"Unknown document type: {document_type_code}"
            
            logger.info(
                f"Document classified as '{document_type_code}' with confidence {confidence:.2f}"
            )
            
            return str(document_type.id), confidence, metadata, None
            
        except Exception as e:
            logger.error(f"Error in document classification: {e}", exc_info=True)
            return None, None, None, str(e)

    @staticmethod
    def _classify_with_llm(
        ocr_text: str,
        file_name: str = None,
        possible_types: list = None
    ) -> Optional[Dict]:
        """
        Classify document using LLM (OpenAI/Anthropic).
        
        Uses a comprehensive prompt that covers all document types, their characteristics,
        and edge cases for accurate classification.
        
        Args:
            ocr_text: Extracted text from OCR
            file_name: Original file name
            possible_types: List of possible document type codes
            
        Returns:
            Dict with 'document_type', 'confidence', 'metadata'
        """
        try:
            # Build comprehensive prompt using helper
            prompt = build_document_classification_prompt(
                ocr_text=ocr_text,
                file_name=file_name,
                possible_types=possible_types
            )
            
            # Get system message
            system_message = get_classification_system_message()
            
            # Call LLM through helper (uses external_services)
            response = call_llm_for_document_processing(
                system_message=system_message,
                user_prompt=prompt,
                model=getattr(settings, "AI_CALLS_LLM_MODEL", "gpt-5.2"),
                temperature=0.1,
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            
            if not response or 'content' not in response:
                logger.error("LLM response missing content")
                return None
            
            # Parse JSON response
            result = parse_llm_json_response(response['content'])
            if not result:
                return None
            
            # Validate result
            if 'document_type' not in result:
                logger.error("LLM response missing document_type")
                return None
            
            confidence = result.get('confidence', 0.5)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                confidence = 0.5
            
            return {
                'document_type': result['document_type'],
                'confidence': float(confidence),
                'metadata': {
                    'reasoning': result.get('reasoning', ''),
                    'model': response.get('model', 'gpt-5.2'),
                    'usage': response.get('usage', {}),
                    'processing_time_ms': response.get('processing_time_ms', 0)
                }
            }
            
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError,
                LLMAPIKeyError, LLMInvalidResponseError) as e:
            logger.error(f"LLM call failed for classification: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM for classification: {e}", exc_info=True)
            return None


    @staticmethod
    def should_auto_classify(confidence: float) -> bool:
        """
        Determine if document should be auto-classified based on confidence.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            True if confidence >= threshold, False otherwise
        """
        return confidence >= DocumentClassificationService.CONFIDENCE_THRESHOLD

