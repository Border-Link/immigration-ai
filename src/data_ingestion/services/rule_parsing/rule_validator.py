"""
Rule validation and inference utilities.

Handles validation of extracted rules and inference of rule types.
"""

import json
import logging
from typing import Dict, Optional, Tuple
from data_ingestion.helpers.requirement_codes import get_requirement_code_category
from data_ingestion.helpers.json_logic_validator import validate_json_logic

logger = logging.getLogger('django')


class RuleValidator:
    """Validates and infers rule types from extracted rule data."""
    
    @staticmethod
    def validate_rule_data(rule_data: Dict) -> Dict:
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
    def infer_rule_type(rule_data: Dict) -> str:
        """
        Infer rule type from rule data using requirement code category.
        
        Args:
            rule_data: Rule data dictionary
            
        Returns:
            Rule type string (fee, document, processing_time, eligibility, other)
        """
        requirement_code = rule_data.get('requirement_code', '').upper()
        description_lower = rule_data.get('description', '').lower()
        
        # Use requirement code category if available
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
    def validate_json_logic(condition_expression: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON Logic expression.
        
        Args:
            condition_expression: JSON Logic expression dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_json_logic(condition_expression)
