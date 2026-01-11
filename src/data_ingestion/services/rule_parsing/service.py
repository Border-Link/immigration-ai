"""
Main Rule Parsing Service.

Public API for AI-assisted rule extraction from document versions.
Orchestrates the parsing workflow using specialized handlers.
"""

import logging
import time
from typing import Dict
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone

from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector
from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector
from data_ingestion.helpers.text_processor import (
    validate_text_for_parsing,
    prepare_text_for_llm
)
from data_ingestion.helpers.rule_parsing_constants import MIN_TEXT_LENGTH
from data_ingestion.exceptions.rule_parsing_exceptions import InsufficientTextError
from data_ingestion.helpers.audit_logger import RuleParsingAuditLogger
from data_ingestion.helpers.json_logic_validator import validate_json_logic

from .llm_handler import LLMHandler
from .rule_validator import RuleValidator
from .rule_scorer import RuleScorer
from .streaming_handler import StreamingHandler
from .batch_processor import BatchProcessor

logger = logging.getLogger('django')

# Cache timeout for LLM responses (24 hours)
LLM_CACHE_TIMEOUT = 60 * 60 * 24


class RuleParsingService:
    """
    Production-ready service for AI-assisted rule extraction from document versions.
    
    Features:
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Transaction safety
    - JSON Logic validation
    - Cost tracking
    - Model version tracking
    - Input validation
    - Caching
    - Rate limiting
    - PII detection and redaction
    - Comprehensive error handling
    - Audit logging
    - Structured metrics
    - Streaming for large documents
    - Parallel batch processing
    """

    @staticmethod
    @transaction.atomic
    def parse_document_version(document_version: DocumentVersion) -> Dict:
        """
        Parse a document version using AI to extract structured rules.
        
        Uses select_for_update to prevent race conditions and ensures
        all database operations are in a transaction.
        
        Args:
            document_version: DocumentVersion instance to parse
            
        Returns:
            Dict with parsing results including:
            - success: bool
            - rules_created: int
            - validation_tasks_created: int
            - tokens_used: int (optional)
            - estimated_cost: float (optional)
            - processing_time_ms: int (optional)
            - error: str (if failed)
        """
        start_time = time.time()
        
        # Log parse started
        RuleParsingAuditLogger.log_parse_started(
            document_version=document_version,
            metadata={'start_time': timezone.now().isoformat()}
        )
        
        try:
            # Check if already parsed (with locking to prevent race conditions)
            existing_rules = ParsedRuleSelector.get_by_document_version(document_version)
            existing_rules = existing_rules.select_for_update()
            
            if existing_rules.exists():
                logger.info(f"Document version {document_version.id} already parsed, skipping")
                return {
                    'success': True,
                    'message': 'Already parsed',
                    'rules_created': existing_rules.count()
                }
            
            # Extract and validate text
            extracted_text = document_version.raw_text
            
            # Get jurisdiction from document version (needed for streaming check)
            jurisdiction = getattr(settings, 'DEFAULT_JURISDICTION', 'UK')
            try:
                if (document_version.source_document and 
                    document_version.source_document.data_source):
                    jurisdiction = document_version.source_document.data_source.jurisdiction
            except Exception as e:
                logger.warning(f"Could not get jurisdiction from document version {document_version.id}: {e}. Using default: {jurisdiction}")
            
            # Check if text is too large for single processing (streaming mode)
            use_streaming = getattr(settings, 'USE_STREAMING_FOR_LARGE_DOCS', True)
            streaming_threshold = getattr(settings, 'STREAMING_THRESHOLD', 10000)  # characters
            
            if use_streaming and len(extracted_text) > streaming_threshold:
                # Use streaming processing for large documents
                logger.info(f"Document version {document_version.id} is large ({len(extracted_text)} chars), using streaming mode")
                return StreamingHandler.parse_document_version_streaming(
                    document_version, extracted_text, jurisdiction
                )
            
            # Prepare text (normalize encoding and redact PII)
            redact_pii = getattr(settings, 'REDACT_PII_BEFORE_LLM', True)
            extracted_text, text_metadata = prepare_text_for_llm(extracted_text, redact_pii=redact_pii)
            
            if text_metadata.get('pii_redacted'):
                logger.info(
                    f"Redacted {text_metadata.get('pii_count', 0)} PII items from "
                    f"document version {document_version.id}"
                )
                # Log PII detection
                RuleParsingAuditLogger.log_pii_detected(
                    document_version=document_version,
                    pii_count=text_metadata.get('pii_count', 0),
                    pii_types=text_metadata.get('pii_types', {})
                )
            
            # Validate text
            is_valid, error_msg = validate_text_for_parsing(extracted_text, MIN_TEXT_LENGTH)
            if not is_valid:
                logger.warning(f"Document version {document_version.id} has invalid text: {error_msg}")
                raise InsufficientTextError(error_msg)
            
            # Check cache first
            cache_key = f"llm_parse:{document_version.content_hash}:{jurisdiction}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached LLM response for document version {document_version.id}")
                # Log cache hit
                RuleParsingAuditLogger.log_cache_hit(
                    document_version=document_version,
                    metadata={'cache_key': cache_key}
                )
                ai_result = cached_result
            else:
                # Call AI/LLM to extract rules
                ai_result = LLMHandler.call_llm_for_rule_extraction(
                    extracted_text, 
                    jurisdiction=jurisdiction,
                    document_version_id=str(document_version.id)
                )
                
                # Cache successful results
                if ai_result.get('success') and ai_result.get('content'):
                    cache.set(cache_key, ai_result, LLM_CACHE_TIMEOUT)
            
            if not ai_result.get('success'):
                error_msg = ai_result.get('error', 'Unknown error')
                logger.error(f"AI parsing failed for document version {document_version.id}: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'error_type': ai_result.get('error_type')
                }
            
            # Process and store parsed rules
            parsed_rules = ai_result.get('rules', [])
            rules_created = 0
            validation_tasks_created = 0
            errors = []
            
            for rule_data in parsed_rules:
                try:
                    # Validate rule data before processing
                    validation_result = RuleValidator.validate_rule_data(rule_data)
                    if not validation_result.get('valid'):
                        error_msg = validation_result.get('error', 'Unknown validation error')
                        logger.warning(f"Skipping invalid rule data: {error_msg}")
                        errors.append(error_msg)
                        continue
                    
                    # Validate JSON Logic
                    condition_expr = rule_data.get('condition_expression', {})
                    is_valid_logic, logic_error = validate_json_logic(condition_expr)
                    if not is_valid_logic:
                        logger.warning(f"Invalid JSON Logic expression: {logic_error}")
                        errors.append(f"Invalid JSON Logic: {logic_error}")
                        continue
                    
                    # Create parsed rule with all metadata
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
                        llm_model=ai_result.get('model'),
                        llm_model_version=None,  # Could extract from model string if available
                        tokens_used=ai_result.get('usage', {}).get('total_tokens'),
                        estimated_cost=ai_result.get('estimated_cost'),
                        processing_time_ms=ai_result.get('processing_time_ms')
                    )
                    
                    if parsed_rule:
                        rules_created += 1
                        
                        # Create validation task (check for duplicates first)
                        if not RuleValidationTaskSelector.exists_for_parsed_rule(parsed_rule):
                            sla_deadline = RuleScorer.calculate_sla_deadline(
                                parsed_rule.confidence_score
                            )
                            
                            RuleValidationTaskRepository.create_validation_task(
                                parsed_rule=parsed_rule,
                                sla_deadline=sla_deadline
                            )
                            validation_tasks_created += 1
                        else:
                            logger.debug(f"Validation task already exists for parsed rule {parsed_rule.id}")
                        
                except Exception as e:
                    logger.error(f"Error creating parsed rule: {e}", exc_info=True)
                    errors.append(str(e))
                    continue
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log metrics
            usage = ai_result.get('usage', {})
            tokens_used_dict = {
                'prompt': usage.get('prompt_tokens'),
                'completion': usage.get('completion_tokens'),
                'total': usage.get('total_tokens')
            }
            RuleParsingService._log_metrics(
                success=True,
                rules_created=rules_created,
                processing_time_ms=processing_time_ms,
                tokens_used=tokens_used_dict,
                jurisdiction=jurisdiction
            )
            
            # Log parse completed
            RuleParsingAuditLogger.log_parse_completed(
                document_version=document_version,
                rules_created=rules_created,
                metadata={
                    'validation_tasks_created': validation_tasks_created,
                    'tokens_used': ai_result.get('usage', {}).get('total_tokens'),
                    'estimated_cost': ai_result.get('estimated_cost'),
                    'processing_time_ms': processing_time_ms,
                    'jurisdiction': jurisdiction,
                    'model': ai_result.get('model'),
                    'errors': errors if errors else None
                }
            )
            
            return {
                'success': True,
                'rules_created': rules_created,
                'validation_tasks_created': validation_tasks_created,
                'tokens_used': ai_result.get('usage', {}).get('total_tokens'),
                'estimated_cost': ai_result.get('estimated_cost'),
                'processing_time_ms': processing_time_ms,
                'errors': errors if errors else None
            }
            
        except InsufficientTextError as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            RuleParsingService._log_metrics(
                success=False,
                error_type=type(e).__name__,
                processing_time_ms=processing_time_ms
            )
            # Log parse failed
            RuleParsingAuditLogger.log_parse_failed(
                document_version=document_version,
                error_type=type(e).__name__,
                error_message=str(e),
                metadata={'processing_time_ms': processing_time_ms}
            )
            logger.error(f"Error parsing document version {document_version.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'processing_time_ms': processing_time_ms
            }
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            RuleParsingService._log_metrics(
                success=False,
                error_type='UnexpectedError',
                processing_time_ms=processing_time_ms
            )
            # Log parse failed
            RuleParsingAuditLogger.log_parse_failed(
                document_version=document_version,
                error_type='UnexpectedError',
                error_message=str(e),
                metadata={'processing_time_ms': processing_time_ms}
            )
            logger.error(f"Unexpected error parsing document version {document_version.id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': 'UnexpectedError',
                'processing_time_ms': processing_time_ms
            }
    
    @staticmethod
    def _log_metrics(
        success: bool,
        rules_created: int = 0,
        processing_time_ms: int = 0,
        tokens_used: int = None,
        jurisdiction: str = None,
        error_type: str = None
    ) -> None:
        """
        Log structured metrics for monitoring.
        
        Args:
            success: Whether parsing was successful
            rules_created: Number of rules created
            processing_time_ms: Processing time in milliseconds
            tokens_used: Number of tokens used
            jurisdiction: Jurisdiction code
            error_type: Type of error if failed
        """
        import json
        from data_ingestion.helpers.metrics import track_document_parsing
        
        # Track Prometheus metrics
        status = 'success' if success else 'failure'
        duration_seconds = processing_time_ms / 1000.0 if processing_time_ms else 0
        jurisdiction_code = jurisdiction or 'unknown'
        
        # Extract token counts if available
        tokens_prompt = None
        tokens_completion = None
        if tokens_used and isinstance(tokens_used, dict):
            tokens_prompt = tokens_used.get('prompt')
            tokens_completion = tokens_used.get('completion')
        elif tokens_used:
            # If it's a single number, assume it's total
            tokens_prompt = tokens_used
        
        # Calculate cost (approximate)
        cost_usd = None
        if tokens_prompt and tokens_completion:
            # Approximate pricing for GPT-4
            cost_usd = (tokens_prompt * 0.00003) + (tokens_completion * 0.00006)
        
        track_document_parsing(
            status=status,
            jurisdiction=jurisdiction_code,
            duration=duration_seconds,
            rules_created=rules_created if success else None,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost_usd=cost_usd
        )
        
        # Also log as structured JSON for backward compatibility
        metrics = {
            'service': 'rule_parsing',
            'success': success,
            'rules_created': rules_created,
            'processing_time_ms': processing_time_ms,
        }
        
        if tokens_used:
            metrics['tokens_used'] = tokens_used
        
        if jurisdiction:
            metrics['jurisdiction'] = jurisdiction
        
        if error_type:
            metrics['error_type'] = error_type
        
        logger.info(f"METRICS: {json.dumps(metrics)}")
    
    # ============================================================================
    # BATCH PROCESSING METHODS (delegated to BatchProcessor)
    # ============================================================================
    
    @staticmethod
    def parse_document_versions_batch(
        document_versions,
        max_concurrent: int = 3,
        continue_on_error: bool = True,
        use_parallel: bool = True
    ) -> Dict:
        """Parse multiple document versions in batch."""
        return BatchProcessor.parse_document_versions_batch(
            document_versions=document_versions,
            max_concurrent=max_concurrent,
            continue_on_error=continue_on_error,
            use_parallel=use_parallel
        )
    
    @staticmethod
    def parse_document_versions_by_ids(
        document_version_ids,
        max_concurrent: int = 3,
        continue_on_error: bool = True
    ) -> Dict:
        """Parse document versions by their IDs."""
        return BatchProcessor.parse_document_versions_by_ids(
            document_version_ids=document_version_ids,
            max_concurrent=max_concurrent,
            continue_on_error=continue_on_error
        )
    
    @staticmethod
    def parse_pending_document_versions(
        limit=None,
        jurisdiction=None,
        max_concurrent: int = 3
    ) -> Dict:
        """Parse pending document versions that haven't been parsed yet."""
        return BatchProcessor.parse_pending_document_versions(
            limit=limit,
            jurisdiction=jurisdiction,
            max_concurrent=max_concurrent
        )
