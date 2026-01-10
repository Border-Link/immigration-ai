"""
Document Content Validation Service

Service for validating document content against case facts.
Checks if document details (names, dates, numbers) match case facts.
"""
import logging
from typing import Tuple, Optional, Dict
from immigration_cases.selectors.case_fact_selector import CaseFactSelector
from document_handling.helpers.prompts import (
    build_content_validation_prompt,
    get_content_validation_system_message
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


class DocumentContentValidationService:
    """
    Service for validating document content against case facts.
    Uses LLM to compare document content with case facts.
    """

    @staticmethod
    def validate_content(
        case_document_id: str,
        ocr_text: str = None,
        extracted_metadata: Dict = None
    ) -> Tuple[str, Optional[Dict], Optional[str]]:
        """
        Validate document content against case facts.
        
        Args:
            case_document_id: UUID of the case document
            ocr_text: Extracted text from OCR (optional, will fetch if not provided)
            extracted_metadata: Extracted metadata from document (optional)
            
        Returns:
            Tuple of (validation_status, validation_details, error_message)
            - validation_status: 'passed', 'failed', 'warning', 'pending'
            - validation_details: Dict with matched/mismatched fields, confidence, etc.
            - error_message: Error message if validation failed
        """
        try:
            # Get case document
            from document_handling.selectors.case_document_selector import CaseDocumentSelector
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            if not case_document:
                return 'pending', None, "Case document not found"
            
            # Get case facts
            case = case_document.case
            case_facts = CaseFactSelector.get_by_case(case)
            
            if not case_facts.exists():
                return 'pending', None, "No case facts available for validation"
            
            # Convert case facts to dictionary
            facts_dict = {}
            for fact in case_facts:
                facts_dict[fact.fact_key] = fact.fact_value
            
            # Get OCR text if not provided
            if not ocr_text:
                ocr_text = case_document.ocr_text
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                return 'pending', None, "Insufficient OCR text for validation"
            
            # Use LLM for content validation
            validation_result = DocumentContentValidationService._validate_with_llm(
                ocr_text=ocr_text,
                case_facts=facts_dict,
                document_type_code=case_document.document_type.code if case_document.document_type else None,
                extracted_metadata=extracted_metadata or case_document.extracted_metadata
            )
            
            if not validation_result:
                return 'pending', None, "LLM validation failed"
            
            validation_status = validation_result.get('status', 'pending')
            validation_details = validation_result.get('details', {})
            
            logger.info(
                f"Content validation completed for document {case_document_id}: "
                f"status={validation_status}"
            )
            
            return validation_status, validation_details, None
            
        except Exception as e:
            logger.error(f"Error in content validation: {e}", exc_info=True)
            return 'pending', None, str(e)

    @staticmethod
    def _validate_with_llm(
        ocr_text: str,
        case_facts: Dict,
        document_type_code: str = None,
        extracted_metadata: Dict = None
    ) -> Optional[Dict]:
        """
        Validate document content using LLM through external_services.
        
        Args:
            ocr_text: Extracted text from OCR
            case_facts: Dictionary of case facts (fact_key -> fact_value)
            document_type_code: Document type code
            extracted_metadata: Extracted metadata from document
            
        Returns:
            Dict with 'status', 'details'
        """
        try:
            # Build comprehensive prompt using helper
            prompt = build_content_validation_prompt(
                ocr_text=ocr_text,
                case_facts=case_facts,
                document_type_code=document_type_code,
                extracted_metadata=extracted_metadata
            )
            
            # Get system message
            system_message = get_content_validation_system_message()
            
            # Call LLM through helper (uses external_services)
            response = call_llm_for_document_processing(
                system_message=system_message,
                user_prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=800,
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
            if 'status' not in result:
                logger.error("LLM response missing status")
                return None
            
            return {
                'status': result.get('status'),
                'details': result.get('details', {}),
                'metadata': {
                    'reasoning': result.get('reasoning', ''),
                    'model': response.get('model', 'gpt-4o-mini'),
                    'usage': response.get('usage', {}),
                    'processing_time_ms': response.get('processing_time_ms', 0)
                }
            }
            
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError,
                LLMAPIKeyError, LLMInvalidResponseError) as e:
            logger.error(f"LLM call failed for content validation: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM for content validation: {e}", exc_info=True)
            return None


    @staticmethod
    def get_validation_summary(validation_details: Dict) -> str:
        """
        Get human-readable validation summary.
        
        Args:
            validation_details: Validation details dictionary
            
        Returns:
            Human-readable summary string
        """
        if not validation_details:
            return "Validation pending"
        
        matched = validation_details.get('matched_fields', [])
        mismatched = validation_details.get('mismatched_fields', [])
        missing = validation_details.get('missing_fields', [])
        summary = validation_details.get('summary', '')
        
        parts = []
        if matched:
            parts.append(f"Matched: {len(matched)} fields")
        if mismatched:
            parts.append(f"Mismatched: {len(mismatched)} fields")
        if missing:
            parts.append(f"Missing: {len(missing)} fields")
        
        result = ", ".join(parts) if parts else "No validation results"
        if summary:
            result += f" - {summary}"
        
        return result
