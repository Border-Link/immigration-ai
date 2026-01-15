"""
LLM interaction handler for rule extraction.

Handles all LLM API calls, response parsing, and rule extraction.
"""

import logging
from typing import Dict, Optional
from external_services.request import ExternalLLMClient
from data_ingestion.helpers.cost_tracker import track_usage
from .response_parser import ResponseParser
from django.conf import settings

logger = logging.getLogger('django')


class LLMHandler:
    """Handles LLM interactions for rule extraction."""
    
    @staticmethod
    def call_llm_for_rule_extraction(
        extracted_text: str,
        jurisdiction: str = 'UK',
        document_version_id: Optional[str] = None
    ) -> Dict:
        """
        Call LLM to extract structured rules from text.
        
        Uses the production-ready LLMClient with retry, timeout, and error handling.
        
        Args:
            extracted_text: Text content to extract rules from
            jurisdiction: Jurisdiction code (UK, US, CA, AU)
            document_version_id: Optional document version ID for tracking
            
        Returns:
            Dict with 'success', 'rules' (list), 'usage', 'model', 'estimated_cost', etc.
        """
        try:
            # Initialize external LLM client (all external requests go through external_services)
            llm_client = ExternalLLMClient()
            
            # Call LLM
            llm_response = llm_client.extract_rules(
                extracted_text=extracted_text,
                jurisdiction=jurisdiction
            )
            
            # Track usage and calculate cost
            usage_data = track_usage(
                model=llm_response.get('model', 'unknown'),
                usage=llm_response.get('usage', {}),
                document_version_id=document_version_id
            )
            
            # Parse JSON response
            parsed_response = ResponseParser.parse_llm_response(
                llm_response.get('content', '')
            )
            
            if not parsed_response:
                return {
                    'success': False,
                    'error': 'Failed to parse LLM response as valid JSON',
                    'error_type': 'InvalidResponse',
                    'model': llm_response.get('model'),
                    'usage': llm_response.get('usage'),
                    'estimated_cost': usage_data.get('estimated_cost'),
                    'processing_time_ms': llm_response.get('processing_time_ms')
                }
            
            # Extract rules from response
            rules = ResponseParser.extract_rules_from_response(parsed_response)
            
            if getattr(settings, "APP_ENV", None) != "test":
                logger.info(f"Extracted {len(rules)} rules from LLM response (model: {llm_response.get('model')})")
            
            return {
                'success': True,
                'rules': rules,
                'model': llm_response.get('model'),
                'usage': llm_response.get('usage'),
                'estimated_cost': usage_data.get('estimated_cost'),
                'processing_time_ms': llm_response.get('processing_time_ms')
            }
            
        except Exception as e:
            error_type = type(e).__name__
            if getattr(settings, "APP_ENV", None) != "test":
                logger.error(f"Error calling LLM for rule extraction: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': error_type
            }
