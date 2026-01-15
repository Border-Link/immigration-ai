"""
Streaming handler for large document processing.

Handles chunked processing of large documents that exceed token limits.
"""

import logging
from typing import Dict
from django.conf import settings
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.helpers.parallel_processor import StreamingProcessor
from data_ingestion.helpers.text_processor import prepare_text_for_llm
from data_ingestion.helpers.rule_parsing_constants import MAX_TEXT_LENGTH
from data_ingestion.helpers.json_logic_validator import validate_json_logic
from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository
from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector
from .response_parser import ResponseParser
from .llm_handler import LLMHandler
from .rule_validator import RuleValidator
from .rule_scorer import RuleScorer

logger = logging.getLogger('django')


class StreamingHandler:
    """Handles streaming/chunked processing of large documents."""
    
    @staticmethod
    def parse_document_version_streaming(
        document_version: DocumentVersion,
        extracted_text: str,
        jurisdiction: str
    ) -> Dict:
        """
        Parse large document version using streaming (chunked processing).
        
        Args:
            document_version: DocumentVersion instance
            extracted_text: Full text content
            jurisdiction: Jurisdiction code
            
        Returns:
            Dict with parsing results
        """
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Using streaming mode for document version {document_version.id}")
        
        # Prepare text
        redact_pii = getattr(settings, 'REDACT_PII_BEFORE_LLM', True)
        extracted_text, text_metadata = prepare_text_for_llm(extracted_text, redact_pii=redact_pii)
        
        # Process in chunks
        chunk_size = MAX_TEXT_LENGTH - 500  # Leave room for prompt
        overlap = 200  # Overlap between chunks
        
        def process_chunk(chunk_text: str) -> Dict:
            """Process a single chunk."""
            # Call LLM for this chunk
            ai_result = LLMHandler.call_llm_for_rule_extraction(
                chunk_text,
                jurisdiction=jurisdiction,
                document_version_id=str(document_version.id)
            )
            
            if ai_result.get('success'):
                parsed_response = ResponseParser.parse_llm_response(
                    ai_result.get('content', '')
                )
                if parsed_response:
                    rules = ResponseParser.extract_rules_from_response(parsed_response)
                    return {
                        'rules': rules,
                        'tokens_used': ai_result.get('usage', {}).get('total_tokens', 0),
                        'estimated_cost': ai_result.get('estimated_cost', 0),
                        'model': ai_result.get('model')
                    }
            
            return {'rules': [], 'tokens_used': 0, 'estimated_cost': 0}
        
        # Process chunks
        chunk_results = StreamingProcessor.process_in_chunks(
            text=extracted_text,
            chunk_size=chunk_size,
            overlap=overlap,
            process_chunk_func=process_chunk
        )
        
        # Merge results
        merged = StreamingProcessor.merge_chunk_results(chunk_results)
        
        # Process and store rules
        all_rules = merged.get('rules', [])
        rules_created = 0
        validation_tasks_created = 0
        errors = []
        
        for rule_data in all_rules:
            try:
                # Validate rule data
                validation_result = RuleValidator.validate_rule_data(rule_data)
                if not validation_result.get('valid'):
                    errors.append(validation_result.get('error', 'Unknown validation error'))
                    continue
                
                # Validate JSON Logic
                condition_expr = rule_data.get('condition_expression', {})
                is_valid_logic, logic_error = validate_json_logic(condition_expr)
                if not is_valid_logic:
                    errors.append(f"Invalid JSON Logic: {logic_error}")
                    continue
                
                # Create parsed rule
                parsed_rule = ParsedRuleRepository.create_parsed_rule(
                    document_version=document_version,
                    visa_code=rule_data.get('visa_code', 'UNKNOWN'),
                    rule_type=RuleValidator.infer_rule_type(rule_data),
                    extracted_logic=condition_expr,
                    description=rule_data.get('description', ''),
                    source_excerpt=rule_data.get('source_excerpt', ''),
                    confidence_score=RuleScorer.compute_confidence_score(
                        rule_data, extracted_text, jurisdiction
                    ),
                    status='pending',
                    llm_model=merged.get('model'),
                    tokens_used=merged.get('tokens_used'),
                    estimated_cost=merged.get('estimated_cost')
                )
                
                if parsed_rule:
                    rules_created += 1
                    
                    if not RuleValidationTaskSelector.exists_for_parsed_rule(parsed_rule):
                        sla_deadline = RuleScorer.calculate_sla_deadline(
                            parsed_rule.confidence_score
                        )
                        RuleValidationTaskRepository.create_validation_task(
                            parsed_rule=parsed_rule,
                            sla_deadline=sla_deadline
                        )
                        validation_tasks_created += 1
                        
            except Exception as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.error(f"Error creating parsed rule from stream: {e}", exc_info=True)
                errors.append(str(e))
                continue
        
        return {
            'success': True,
            'rules_created': rules_created,
            'validation_tasks_created': validation_tasks_created,
            'tokens_used': merged.get('tokens_used'),
            'estimated_cost': merged.get('estimated_cost'),
            'chunks_processed': len(chunk_results),
            'streaming_mode': True,
            'errors': errors if errors else None
        }
