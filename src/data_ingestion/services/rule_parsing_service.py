import json
import logging
from typing import Dict, List, Optional
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('django')


class RuleParsingService:
    """
    Service for AI-assisted rule extraction from document versions.
    Calls LLM to extract structured rules and stores them in parsed_rules.
    Based on implementation.md Section 5.4.
    """

    @staticmethod
    def parse_document_version(document_version: DocumentVersion) -> Dict:
        """
        Parse a document version using AI to extract structured rules.
        
        Args:
            document_version: DocumentVersion instance to parse
            
        Returns:
            Dict with parsing results
        """
        try:
            # Check if already parsed (avoid duplicate parsing)
            existing_rules = ParsedRuleSelector.get_by_document_version(document_version)
            if existing_rules.exists():
                logger.info(f"Document version {document_version.id} already parsed, skipping")
                return {
                    'success': True,
                    'message': 'Already parsed',
                    'rules_created': existing_rules.count()
                }
            
            # Extract text from document version
            extracted_text = document_version.raw_text
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                logger.warning(f"Document version {document_version.id} has insufficient text for parsing")
                return {
                    'success': False,
                    'message': 'Insufficient text for parsing'
                }
            
            # Call AI/LLM to extract rules
            ai_result = RuleParsingService._call_llm_for_rule_extraction(extracted_text)
            
            if not ai_result.get('success'):
                logger.error(f"AI parsing failed for document version {document_version.id}: {ai_result.get('error')}")
                return ai_result
            
            # Process and store parsed rules
            parsed_rules = ai_result.get('rules', [])
            rules_created = 0
            validation_tasks_created = 0
            
            for rule_data in parsed_rules:
                try:
                    # Create parsed rule
                    parsed_rule = ParsedRuleRepository.create_parsed_rule(
                        document_version=document_version,
                        visa_code=rule_data.get('visa_code', 'UNKNOWN'),
                        rule_type=RuleParsingService._infer_rule_type(rule_data),
                        extracted_logic=rule_data.get('condition_expression', {}),
                        description=rule_data.get('description', ''),
                        source_excerpt=rule_data.get('source_excerpt', ''),
                        confidence_score=RuleParsingService._compute_confidence_score(
                            rule_data, extracted_text
                        ),
                        status='pending'
                    )
                    
                    if parsed_rule:
                        rules_created += 1
                        
                        # Create validation task
                        sla_deadline = RuleParsingService._calculate_sla_deadline(
                            parsed_rule.confidence_score
                        )
                        
                        RuleValidationTaskRepository.create_validation_task(
                            parsed_rule=parsed_rule,
                            sla_deadline=sla_deadline
                        )
                        validation_tasks_created += 1
                        
                except Exception as e:
                    logger.error(f"Error creating parsed rule: {e}")
                    continue
            
            return {
                'success': True,
                'rules_created': rules_created,
                'validation_tasks_created': validation_tasks_created
            }
            
        except Exception as e:
            logger.error(f"Error parsing document version {document_version.id}: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    @staticmethod
    def _call_llm_for_rule_extraction(extracted_text: str) -> Dict:
        """
        Call LLM to extract structured rules from text.
        Based on implementation.md Section 5.4 prompt template.
        
        Args:
            extracted_text: Text content to extract rules from
            
        Returns:
            Dict with 'success', 'rules' (list), or 'error'
        """
        try:
            # TODO: Integrate with actual LLM service when available
            # For now, return a placeholder structure
            # This should be replaced with actual LLM API call
            
            # Prompt template from implementation.md
            prompt = f"""You are an immigration rule extraction system. Extract structured eligibility 
requirements from the following UK immigration rule text.

Rules:
1. Only extract explicitly stated requirements
2. Do not infer or assume
3. Output JSON with this structure:
{{
  "visa_code": "SKILLED_WORKER",
  "requirements": [
    {{
      "requirement_code": "MIN_SALARY",
      "description": "Minimum salary threshold",
      "condition_expression": {{">=": [{{"var": "salary"}, 38700]}},
      "source_excerpt": "Applicants must earn at least £38,700 per year"
    }}
  ]
}}

Text to extract from:
{extracted_text[:5000]}"""  # Limit to 5000 chars for now
            
            # Placeholder: This should call actual LLM service
            # For now, return empty rules (will be implemented when LLM service is available)
            logger.info("LLM rule extraction called (placeholder - needs LLM service integration)")
            
            return {
                'success': True,
                'rules': []  # Empty for now, will be populated when LLM service is integrated
            }
            
        except Exception as e:
            logger.error(f"Error calling LLM for rule extraction: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def _infer_rule_type(rule_data: Dict) -> str:
        """Infer rule type from rule data."""
        description_lower = rule_data.get('description', '').lower()
        requirement_code = rule_data.get('requirement_code', '').upper()
        
        if 'fee' in description_lower or 'cost' in description_lower:
            return 'fee'
        elif 'time' in description_lower or 'day' in description_lower or 'week' in description_lower:
            return 'processing_time'
        elif 'document' in description_lower or 'DOCUMENT' in requirement_code:
            return 'document'
        elif 'MIN_' in requirement_code or 'REQUIREMENT' in requirement_code:
            return 'eligibility'
        else:
            return 'other'

    @staticmethod
    def _compute_confidence_score(rule_data: Dict, source_text: str) -> float:
        """
        Compute confidence score for extracted rule.
        Based on implementation.md Section 5.4 confidence scoring.
        """
        score = 0.5  # Base score
        
        # Validate numeric values
        import re
        condition_expr = rule_data.get('condition_expression', {})
        condition_str = json.dumps(condition_expr)
        numeric_values_in_logic = re.findall(r'\d+', condition_str)
        
        if numeric_values_in_logic:
            # Check if numeric values appear in source text
            for num in numeric_values_in_logic:
                if num in source_text:
                    score += 0.2
                    break
        
        # Validate requirement codes (standard codes)
        standard_codes = ['MIN_SALARY', 'SPONSOR_LICENSE', 'DOCUMENT_REQUIRED', 'FEE_AMOUNT']
        requirement_code = rule_data.get('requirement_code', '')
        if requirement_code in standard_codes:
            score += 0.2
        
        # Validate JSON Logic expression
        try:
            json.dumps(condition_expr)  # Validate it's valid JSON
            if condition_expr:  # Not empty
                score += 0.1
        except:
            pass
        
        # Cap at 1.0
        return min(score, 1.0)

    @staticmethod
    def _calculate_sla_deadline(confidence_score: float) -> timezone.datetime:
        """
        Calculate SLA deadline based on confidence score and change type.
        Based on implementation.md Section 5.5 SLA handling.
        """
        # Default SLA: 7 days
        # Urgent changes (high confidence or requirement changes): 2 days
        if confidence_score > 0.9:
            days = 2  # High confidence = urgent
        else:
            days = 7  # Default
        
        return timezone.now() + timedelta(days=days)

