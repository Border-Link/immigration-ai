"""
Document Classification Service

Service for classifying document types using AI/LLM.
Uses OCR text and file metadata to predict document type.
"""
import logging
from typing import Tuple, Optional, Dict
from django.conf import settings
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector
from document_handling.helpers.prompts import build_document_classification_prompt, get_system_message

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
            # Import OpenAI client
            try:
                from openai import OpenAI
            except ImportError:
                logger.error("OpenAI package not installed. Install with: pip install openai")
                return None
            
            # Get API key from settings
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                logger.error("OPENAI_API_KEY not set in settings")
                return None
            
            client = OpenAI(api_key=api_key)
            
            # Build comprehensive prompt using helper
            prompt = build_document_classification_prompt(
                ocr_text=ocr_text,
                file_name=file_name,
                possible_types=possible_types
            )
            
            # Call LLM
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for classification
                messages=[
                    {
                        "role": "system", 
                        "content": get_system_message()
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=300  # Increased for detailed reasoning
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            import json
            result = json.loads(response_text)
            
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
                    'model': 'gpt-4o-mini'
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
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

