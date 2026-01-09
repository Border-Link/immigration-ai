"""
Production-ready Rule Parsing Service for AI-assisted rule extraction.

This service provides comprehensive rule extraction from document versions using LLM,
with all production-ready improvements including:
- Retry logic with exponential backoff
- Timeout configuration
- Transaction safety
- JSON Logic validation
- Error classification
- Model version tracking
- Cost tracking
- Circuit breaker
- Rate limiting
- Input validation
- Caching
- Metrics
- PII detection and redaction
- Audit logging
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector
from data_ingestion.selectors.rule_validation_task_selector import RuleValidationTaskSelector
from data_ingestion.helpers.llm_client import LLMClient
from data_ingestion.helpers.json_logic_validator import validate_json_logic
from data_ingestion.helpers.cost_tracker import track_usage
from data_ingestion.helpers.text_processor import (
    normalize_text_encoding,
    validate_text_for_parsing,
    prepare_text_for_llm
)
from data_ingestion.helpers.requirement_codes import (
    is_standard_requirement_code,
    get_requirement_code_category
)
from data_ingestion.helpers.confidence_scorer import compute_confidence_score as compute_enhanced_confidence_score
from data_ingestion.helpers.parallel_processor import ParallelProcessor, StreamingProcessor
from data_ingestion.helpers.rule_parsing_constants import (
    MIN_TEXT_LENGTH,
    BASE_CONFIDENCE_SCORE,
    NUMERIC_VALUE_MATCH_BONUS,
    STANDARD_CODE_BONUS,
    VALID_JSON_LOGIC_BONUS,
    MAX_CONFIDENCE_SCORE,
    DEFAULT_SLA_DAYS,
    URGENT_SLA_DAYS,
    HIGH_CONFIDENCE_THRESHOLD,
)
from data_ingestion.exceptions.rule_parsing_exceptions import (
    RuleParsingError,
    InsufficientTextError,
    RuleValidationError,
    DuplicateParsingError,
    JSONLogicValidationError,
)
from data_ingestion.helpers.audit_logger import RuleParsingAuditLogger

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
                return RuleParsingService._parse_document_version_streaming(
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
                ai_result = RuleParsingService._call_llm_for_rule_extraction(
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
                    validation_result = RuleParsingService._validate_rule_data(rule_data)
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
                        rule_type=RuleParsingService._infer_rule_type(rule_data),
                        extracted_logic=condition_expr,
                        description=rule_data.get('description', ''),
                        source_excerpt=rule_data.get('source_excerpt', ''),
                        confidence_score=RuleParsingService._compute_confidence_score(
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
                            sla_deadline = RuleParsingService._calculate_sla_deadline(
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
            RuleParsingService._log_metrics(
                success=True,
                rules_created=rules_created,
                processing_time_ms=processing_time_ms,
                tokens_used=ai_result.get('usage', {}).get('total_tokens'),
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
            
        except (InsufficientTextError, RuleValidationError, DuplicateParsingError) as e:
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
    def _call_llm_for_rule_extraction(
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
            # Initialize LLM client
            llm_client = LLMClient()
            
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
            parsed_response = RuleParsingService._parse_llm_response(
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
            rules = RuleParsingService._extract_rules_from_response(parsed_response)
            
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
            logger.error(f"Error calling LLM for rule extraction: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': error_type
            }
    
    @staticmethod
    def _parse_llm_response(llm_response: str) -> Optional[Dict]:
        """
        Parse LLM response and extract JSON.
        Handles cases where LLM wraps JSON in markdown or adds extra text.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        if not llm_response or not llm_response.strip():
            logger.error("Empty LLM response received")
            return None
        
        try:
            # Try direct JSON parsing first (most common case with response_format)
            return json.loads(llm_response.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?})\s*```', llm_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in the response using balanced braces
        start_pos = llm_response.find('{')
        if start_pos != -1:
            brace_count = 0
            for i in range(start_pos, len(llm_response)):
                if llm_response[i] == '{':
                    brace_count += 1
                elif llm_response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_candidate = llm_response[start_pos:i+1]
                        try:
                            return json.loads(json_candidate)
                        except json.JSONDecodeError:
                            break
        
        # Last resort: try regex
        json_match = re.search('\{[^{}]*(?:\{[^{}]*}[^{}]*)*}', llm_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Could not parse LLM response as JSON. Response preview: {llm_response[:500]}")
        return None
    
    @staticmethod
    def _extract_rules_from_response(parsed_response: Dict) -> List[Dict]:
        """
        Extract rules from parsed LLM response.
        
        Args:
            parsed_response: Parsed JSON response from LLM
            
        Returns:
            List of rule dictionaries
        """
        rules = []
        
        if isinstance(parsed_response, dict):
            if 'requirements' in parsed_response:
                visa_code = parsed_response.get('visa_code', 'UNKNOWN')
                requirements = parsed_response.get('requirements', [])
                
                if not isinstance(requirements, list):
                    logger.warning("Requirements is not a list, converting")
                    requirements = [requirements] if requirements else []
                
                for req in requirements:
                    if isinstance(req, dict):
                        rule = {
                            'visa_code': visa_code,
                            'requirement_code': req.get('requirement_code', 'UNKNOWN'),
                            'description': req.get('description', ''),
                            'condition_expression': req.get('condition_expression', {}),
                            'source_excerpt': req.get('source_excerpt', '')
                        }
                        rules.append(rule)
                    else:
                        logger.warning(f"Invalid requirement format: {req}")
            
            elif 'requirement_code' in parsed_response:
                rules.append({
                    'visa_code': parsed_response.get('visa_code', 'UNKNOWN'),
                    'requirement_code': parsed_response.get('requirement_code', 'UNKNOWN'),
                    'description': parsed_response.get('description', ''),
                    'condition_expression': parsed_response.get('condition_expression', {}),
                    'source_excerpt': parsed_response.get('source_excerpt', '')
                })
        
        if not rules:
            logger.warning(f"No rules extracted from response: {parsed_response}")
        
        return rules

    @staticmethod
    def _validate_rule_data(rule_data: Dict) -> Dict:
        """
        Validate rule data before processing.
        
        Args:
            rule_data: Rule data dictionary to validate
            
        Returns:
            Dict with 'valid' (bool) and optional 'error' (str)
        """
        if not isinstance(rule_data, dict):
            return {'valid': False, 'error': 'Rule data must be a dictionary'}
        
        requirement_code = rule_data.get('requirement_code', '').strip()
        description = rule_data.get('description', '').strip()
        condition_expression = rule_data.get('condition_expression', {})
        
        if not requirement_code:
            return {'valid': False, 'error': 'Missing requirement_code'}
        
        if not description:
            return {'valid': False, 'error': 'Missing description'}
        
        if not condition_expression:
            return {'valid': False, 'error': 'Missing or empty condition_expression'}
        
        if not isinstance(condition_expression, dict):
            return {'valid': False, 'error': 'condition_expression must be a dictionary'}
        
        # Validate JSON serializability
        try:
            json.dumps(condition_expression)
        except (TypeError, ValueError) as e:
            return {'valid': False, 'error': f'Invalid condition_expression: {str(e)}'}
        
        return {'valid': True}
    
    @staticmethod
    def _infer_rule_type(rule_data: Dict) -> str:
        """
        Infer rule type from rule data using requirement code category.
        
        Args:
            rule_data: Rule data dictionary
            
        Returns:
            Rule type string
        """
        requirement_code = rule_data.get('requirement_code', '').upper()
        description_lower = rule_data.get('description', '').lower()
        
        category = get_requirement_code_category(requirement_code)
        
        if category == 'fee':
            return 'fee'
        elif category == 'document':
            return 'document'
        elif category == 'processing_time':
            return 'processing_time'
        elif category in ['salary', 'age', 'experience', 'sponsor', 'language', 
                         'financial', 'nationality', 'health', 'character', 
                         'employment', 'family']:
            return 'eligibility'
        
        # Fallback to description-based inference
        if 'fee' in description_lower or 'cost' in description_lower or 'charge' in description_lower:
            return 'fee'
        elif 'time' in description_lower or 'day' in description_lower or 'week' in description_lower or 'month' in description_lower:
            return 'processing_time'
        elif 'document' in description_lower or 'certificate' in description_lower or 'proof' in description_lower:
            return 'document'
        elif 'MIN_' in requirement_code or 'MAX_' in requirement_code or 'REQUIREMENT' in requirement_code:
            return 'eligibility'
        else:
            return 'other'

    @staticmethod
    def _compute_confidence_score(
        rule_data: Dict,
        source_text: str,
        jurisdiction: Optional[str] = None
    ) -> float:
        """
        Compute enhanced confidence score for extracted rule.
        
        Uses multi-factor scoring with support for ML-based scoring.
        
        Args:
            rule_data: Rule data dictionary
            source_text: Original source text for validation
            jurisdiction: Optional jurisdiction code for pattern matching
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Use enhanced confidence scorer
        return compute_enhanced_confidence_score(
            rule_data=rule_data,
            source_text=source_text,
            jurisdiction=jurisdiction,
            use_ml=False  # Can be enabled when ML model is available
        )

    @staticmethod
    def _calculate_sla_deadline(confidence_score: float) -> timezone.datetime:
        """
        Calculate SLA deadline based on confidence score.
        
        Args:
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            Datetime for SLA deadline
        """
        if confidence_score >= HIGH_CONFIDENCE_THRESHOLD:
            days = URGENT_SLA_DAYS
        else:
            days = DEFAULT_SLA_DAYS
        
        return timezone.now() + timedelta(days=days)
    
    @staticmethod
    def _log_metrics(
        success: bool,
        rules_created: int = 0,
        processing_time_ms: int = 0,
        tokens_used: Optional[int] = None,
        jurisdiction: Optional[str] = None,
        error_type: Optional[str] = None
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
        
        # Log as structured JSON for easy parsing
        logger.info(f"METRICS: {json.dumps(metrics)}")
        
        # Could also send to metrics service (Prometheus, Datadog, etc.)
        # Example:
        # prometheus_metrics.rule_parsing_duration.observe(processing_time_ms / 1000)
        # prometheus_metrics.rule_parsing_success.inc() if success else prometheus_metrics.rule_parsing_failure.inc()
    
    @staticmethod
    def _parse_document_version_streaming(
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
        from data_ingestion.helpers.rule_parsing_constants import MAX_TEXT_LENGTH
        
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
            ai_result = RuleParsingService._call_llm_for_rule_extraction(
                chunk_text,
                jurisdiction=jurisdiction,
                document_version_id=str(document_version.id)
            )
            
            if ai_result.get('success'):
                parsed_response = RuleParsingService._parse_llm_response(
                    ai_result.get('content', '')
                )
                if parsed_response:
                    rules = RuleParsingService._extract_rules_from_response(parsed_response)
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
                validation_result = RuleParsingService._validate_rule_data(rule_data)
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
                    rule_type=RuleParsingService._infer_rule_type(rule_data),
                    extracted_logic=condition_expr,
                    description=rule_data.get('description', ''),
                    source_excerpt=rule_data.get('source_excerpt', ''),
                    confidence_score=RuleParsingService._compute_confidence_score(
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
                        sla_deadline = RuleParsingService._calculate_sla_deadline(
                            parsed_rule.confidence_score
                        )
                        RuleValidationTaskRepository.create_validation_task(
                            parsed_rule=parsed_rule,
                            sla_deadline=sla_deadline
                        )
                        validation_tasks_created += 1
                        
            except Exception as e:
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
    
    # ============================================================================
    # BATCH PROCESSING METHODS
    # ============================================================================
    
    @staticmethod
    def parse_document_versions_batch(
        document_versions: List[DocumentVersion],
        max_concurrent: int = 3,
        continue_on_error: bool = True,
        use_parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Parse multiple document versions in batch with parallel processing.
        
        Args:
            document_versions: List of DocumentVersion instances to parse
            max_concurrent: Maximum concurrent parsing operations
            continue_on_error: Whether to continue processing on errors
            use_parallel: Whether to use parallel processing (default: True)
            
        Returns:
            Dict with:
            - total: Total documents
            - successful: Number successfully parsed
            - failed: Number failed
            - skipped: Number skipped (already parsed)
            - results: List of individual results
            - summary: Summary statistics
        """
        total = len(document_versions)
        
        logger.info(f"Starting batch parsing for {total} document versions (parallel={use_parallel}, workers={max_concurrent})")
        
        if use_parallel and total > 1:
            # Use parallel processing
            def process_doc(doc_version):
                """Process a single document version."""
                try:
                    result = RuleParsingService.parse_document_version(doc_version)
                    result['document_version_id'] = str(doc_version.id)
                    return result
                except Exception as e:
                    logger.error(f"Error processing document version {doc_version.id}: {e}", exc_info=True)
                    return {
                        'document_version_id': str(doc_version.id),
                        'success': False,
                        'error': str(e),
                        'error_type': 'UnexpectedError'
                    }
            
            # Process in parallel
            parallel_results = ParallelProcessor.process_in_parallel(
                items=document_versions,
                process_func=process_doc,
                max_workers=max_concurrent,
                continue_on_error=continue_on_error
            )
            
            # Extract results
            results = [r['result'] for r in parallel_results if r['result']]
            
            # Add indices
            for idx, result in enumerate(results, 1):
                result['index'] = idx
        else:
            # Sequential processing (fallback or for single item)
            results = []
            for idx, doc_version in enumerate(document_versions, 1):
                try:
                    logger.info(f"Processing document {idx}/{total}: {doc_version.id}")
                    
                    result = RuleParsingService.parse_document_version(doc_version)
                    result['document_version_id'] = str(doc_version.id)
                    result['index'] = idx
                    results.append(result)
                    
                    if not result.get('success') and not continue_on_error:
                        logger.error(f"Stopping batch processing due to error in document {doc_version.id}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing document version {doc_version.id}: {e}", exc_info=True)
                    results.append({
                        'document_version_id': str(doc_version.id),
                        'index': idx,
                        'success': False,
                        'error': str(e),
                        'error_type': 'UnexpectedError'
                    })
                    if not continue_on_error:
                        break
        
        # Calculate statistics
        successful = sum(1 for r in results if r.get('success') and r.get('message') != 'Already parsed')
        failed = sum(1 for r in results if not r.get('success'))
        skipped = sum(1 for r in results if r.get('success') and r.get('message') == 'Already parsed')
        
        total_rules = sum(r.get('rules_created', 0) for r in results if r.get('success'))
        total_tokens = sum(r.get('tokens_used', 0) or 0 for r in results if r.get('success'))
        total_cost = sum(r.get('estimated_cost', 0) or 0 for r in results if r.get('success'))
        successful_results = [r for r in results if r.get('success') and r.get('message') != 'Already parsed']
        avg_processing_time = sum(
            r.get('processing_time_ms', 0) for r in successful_results
        ) / max(len(successful_results), 1)
        
        summary = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'total_rules_created': total_rules,
            'total_tokens_used': total_tokens,
            'total_estimated_cost': round(total_cost, 6),
            'average_processing_time_ms': round(avg_processing_time, 2),
            'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
            'parallel_processing': use_parallel
        }
        
        logger.info(
            f"Batch parsing completed: {successful} successful, {failed} failed, "
            f"{skipped} skipped out of {total} total"
        )
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'results': results,
            'summary': summary
        }
    
    @staticmethod
    def parse_document_versions_by_ids(
        document_version_ids: List[str],
        max_concurrent: int = 3,
        continue_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Parse multiple document versions by their IDs.
        
        Args:
            document_version_ids: List of document version UUIDs
            max_concurrent: Maximum concurrent parsing operations (reserved for future async)
            continue_on_error: Whether to continue processing on errors
            
        Returns:
            Dict with batch processing results
        """
        from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
        
        document_versions = []
        not_found = []
        
        for doc_id in document_version_ids:
            try:
                doc_version = DocumentVersionSelector.get_by_id(doc_id)
                document_versions.append(doc_version)
            except Exception as e:
                logger.warning(f"Document version {doc_id} not found: {e}")
                not_found.append(doc_id)
        
        if not_found:
            logger.warning(f"{len(not_found)} document versions not found: {not_found}")
        
        result = RuleParsingService.parse_document_versions_batch(
            document_versions=document_versions,
            max_concurrent=max_concurrent,
            continue_on_error=continue_on_error
        )
        
        if not_found:
            result['not_found'] = not_found
        
        return result
    
    @staticmethod
    def parse_pending_document_versions(
        limit: Optional[int] = None,
        jurisdiction: Optional[str] = None,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Parse all pending document versions (not yet parsed).
        
        Args:
            limit: Maximum number of documents to process (None = all)
            jurisdiction: Filter by jurisdiction (None = all)
            max_concurrent: Maximum concurrent parsing operations (reserved for future async)
            
        Returns:
            Dict with batch processing results
        """
        from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
        
        # Get all document versions
        if jurisdiction:
            # Filter by jurisdiction through data source
            document_versions = DocumentVersionSelector.get_by_jurisdiction(jurisdiction)
        else:
            document_versions = DocumentVersionSelector.get_all()
        
        # Filter out already parsed ones
        pending_versions = []
        for doc_version in document_versions:
            existing_rules = ParsedRuleSelector.get_by_document_version(doc_version)
            if not existing_rules.exists():
                pending_versions.append(doc_version)
                if limit and len(pending_versions) >= limit:
                    break
        
        logger.info(f"Found {len(pending_versions)} pending document versions to parse")
        
        return RuleParsingService.parse_document_versions_batch(
            document_versions=pending_versions,
            max_concurrent=max_concurrent,
            continue_on_error=True
        )
