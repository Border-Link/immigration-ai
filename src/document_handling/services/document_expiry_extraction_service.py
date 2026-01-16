"""
Document Expiry Extraction Service

Service for extracting expiry dates from documents using AI/LLM.
Analyzes OCR text to find and extract expiry dates (passport, visa, etc.).
"""
import logging
from typing import Tuple, Optional, Dict
from datetime import date, timedelta
from django.conf import settings
from dateutil import parser as date_parser
from document_handling.helpers.prompts import (
    build_expiry_date_extraction_prompt,
    get_expiry_extraction_system_message
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


class DocumentExpiryExtractionService:
    """
    Service for extracting expiry dates from documents.
    Uses LLM to analyze OCR text and extract expiry dates.
    """

    @staticmethod
    def extract_expiry_date(
        ocr_text: str,
        document_type_code: str = None,
        file_name: str = None
    ) -> Tuple[Optional[date], Optional[float], Optional[Dict], Optional[str]]:
        """
        Extract expiry date from document using AI.
        
        Args:
            ocr_text: Extracted text from OCR
            document_type_code: Document type code (e.g., 'passport', 'visa')
            file_name: Original file name
            
        Returns:
            Tuple of (expiry_date, confidence_score, metadata, error_message)
            - expiry_date: Extracted expiry date (date object) or None
            - confidence_score: Confidence score (0.0 to 1.0)
            - metadata: Additional extraction metadata
            - error_message: Error message if extraction failed
        """
        try:
            if not ocr_text or len(ocr_text.strip()) < 10:
                return None, None, None, "Insufficient OCR text for expiry date extraction"
            
            # Use LLM for expiry date extraction
            extraction_result = DocumentExpiryExtractionService._extract_with_llm(
                ocr_text=ocr_text,
                document_type_code=document_type_code,
                file_name=file_name
            )
            
            if not extraction_result:
                return None, None, None, "LLM extraction failed"
            
            expiry_date_str = extraction_result.get('expiry_date')
            confidence = extraction_result.get('confidence', 0.0)
            metadata = extraction_result.get('metadata', {})
            
            # Parse expiry date
            expiry_date = None
            if expiry_date_str:
                try:
                    # Try parsing the date string
                    parsed_date = date_parser.parse(expiry_date_str, fuzzy=False)
                    expiry_date = parsed_date.date()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse expiry date '{expiry_date_str}': {e}")
                    return None, confidence, metadata, f"Invalid date format: {expiry_date_str}"
            
            logger.info(
                f"Expiry date extracted: {expiry_date} with confidence {confidence:.2f}"
            )
            
            return expiry_date, confidence, metadata, None
            
        except Exception as e:
            logger.error(f"Error in expiry date extraction: {e}", exc_info=True)
            return None, None, None, str(e)

    @staticmethod
    def _extract_with_llm(
        ocr_text: str,
        document_type_code: str = None,
        file_name: str = None
    ) -> Optional[Dict]:
        """
        Extract expiry date using LLM through external_services.
        
        Args:
            ocr_text: Extracted text from OCR
            document_type_code: Document type code
            file_name: Original file name
            
        Returns:
            Dict with 'expiry_date', 'confidence', 'metadata'
        """
        try:
            # Build comprehensive prompt using helper
            prompt = build_expiry_date_extraction_prompt(
                ocr_text=ocr_text,
                document_type_code=document_type_code,
                file_name=file_name
            )
            
            # Get system message
            system_message = get_expiry_extraction_system_message()
            
            # Call LLM through helper (uses external_services)
            response = call_llm_for_document_processing(
                system_message=system_message,
                user_prompt=prompt,
                model=getattr(settings, "AI_CALLS_LLM_MODEL", "gpt-5.2"),
                temperature=0.1,
                max_tokens=300,
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
            if 'expiry_date' not in result:
                logger.error("LLM response missing expiry_date")
                return None
            
            confidence = result.get('confidence', 0.5)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                confidence = 0.5
            
            return {
                'expiry_date': result.get('expiry_date'),
                'confidence': float(confidence),
                'metadata': {
                    'reasoning': result.get('reasoning', ''),
                    'model': response.get('model', 'gpt-5.2'),
                    'extracted_text': result.get('extracted_text', ''),
                    'date_format_detected': result.get('date_format_detected'),
                    'alternative_dates_found': result.get('alternative_dates_found', []),
                    'usage': response.get('usage', {}),
                    'processing_time_ms': response.get('processing_time_ms', 0)
                }
            }
            
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError,
                LLMAPIKeyError, LLMInvalidResponseError) as e:
            logger.error(f"LLM call failed for expiry extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM for expiry extraction: {e}", exc_info=True)
            return None


    @staticmethod
    def is_expired(expiry_date: date, buffer_days: int = 0) -> bool:
        """
        Check if expiry date has passed.
        
        Args:
            expiry_date: Expiry date to check
            buffer_days: Number of days before expiry to consider as expired (default: 0)
            
        Returns:
            True if expired, False otherwise
        """
        if not expiry_date:
            return False
        
        today = date.today()
        expiry_with_buffer = expiry_date - timedelta(days=buffer_days)
        return today > expiry_with_buffer

    @staticmethod
    def days_until_expiry(expiry_date: date) -> Optional[int]:
        """
        Calculate days until expiry.
        
        Args:
            expiry_date: Expiry date
            
        Returns:
            Number of days until expiry (negative if expired), or None if no date
        """
        if not expiry_date:
            return None
        
        today = date.today()
        delta = expiry_date - today
        return delta.days
