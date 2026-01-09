"""
Rule validation and inference utilities.

Handles validation of extracted rules and inference of rule types.
"""

import json
import re
import logging
from typing import Dict, Optional, Tuple, List
from data_ingestion.helpers.requirement_codes import get_requirement_code_category, is_standard_requirement_code
from data_ingestion.helpers.json_logic_validator import validate_json_logic
from data_ingestion.helpers.rule_parsing_constants import (
    REQUIRED_RULE_FIELDS,
    VALID_JSON_LOGIC_OPERATORS
)

logger = logging.getLogger('django')

# Model constraints
VISA_CODE_MAX_LENGTH = 100
DESCRIPTION_MIN_LENGTH = 10
SOURCE_EXCERPT_MIN_LENGTH = 5
REQUIREMENT_CODE_MAX_LENGTH = 100

# Valid rule types from ParsedRule model
VALID_RULE_TYPES = ['eligibility', 'document', 'fee', 'processing_time', 'other']


class RuleValidator:
    """Validates and infers rule types from extracted rule data."""
    
    @staticmethod
    def validate_rule_data(rule_data: Dict) -> Dict:
        """
        Comprehensive validation of rule data before processing.
        
        Args:
            rule_data: Rule data dictionary to validate
            
        Returns:
            Dict with 'valid' (bool) and optional 'error' (str) and 'warnings' (list)
        """
        errors = []
        warnings = []
        
        # 1. Type check
        if not isinstance(rule_data, dict):
            return {'valid': False, 'error': 'Rule data must be a dictionary'}
        
        # 2. Check required fields
        for field in REQUIRED_RULE_FIELDS:
            if field not in rule_data:
                errors.append(f'Missing required field: {field}')
                continue
            
            value = rule_data.get(field)
            if value is None:
                errors.append(f'Required field {field} cannot be None')
        
        if errors:
            return {'valid': False, 'error': '; '.join(errors)}
        
        # 3. Validate requirement_code
        requirement_code = rule_data.get('requirement_code', '').strip()
        if not requirement_code:
            errors.append('Missing requirement_code')
        elif len(requirement_code) > REQUIREMENT_CODE_MAX_LENGTH:
            errors.append(f'requirement_code exceeds maximum length of {REQUIREMENT_CODE_MAX_LENGTH} characters')
        elif not RuleValidator._validate_requirement_code_format(requirement_code):
            warnings.append(f'requirement_code "{requirement_code}" does not follow standard naming convention (UPPERCASE_WITH_UNDERSCORES)')
        
        # 4. Validate description
        description = rule_data.get('description', '').strip()
        if not description:
            errors.append('Missing description')
        elif len(description) < DESCRIPTION_MIN_LENGTH:
            errors.append(f'description must be at least {DESCRIPTION_MIN_LENGTH} characters')
        elif not description or description.isspace():
            errors.append('description cannot be only whitespace')
        
        # 5. Validate condition_expression
        condition_expression = rule_data.get('condition_expression', {})
        if not condition_expression:
            errors.append('Missing or empty condition_expression')
        elif not isinstance(condition_expression, dict):
            errors.append('condition_expression must be a dictionary')
        else:
            # Validate JSON serializability
            try:
                json.dumps(condition_expression)
            except (TypeError, ValueError) as e:
                errors.append(f'Invalid condition_expression: {str(e)}')
        
        # 6. Validate visa_code (if present)
        visa_code = rule_data.get('visa_code', '').strip()
        if visa_code:
            if len(visa_code) > VISA_CODE_MAX_LENGTH:
                errors.append(f'visa_code exceeds maximum length of {VISA_CODE_MAX_LENGTH} characters')
            elif visa_code == 'UNKNOWN':
                warnings.append('visa_code is "UNKNOWN" - consider extracting from source text')
        else:
            warnings.append('visa_code is missing - will default to "UNKNOWN"')
        
        # 7. Validate source_excerpt (if present)
        source_excerpt = rule_data.get('source_excerpt', '').strip()
        if source_excerpt:
            if len(source_excerpt) < SOURCE_EXCERPT_MIN_LENGTH:
                warnings.append(f'source_excerpt is very short (minimum recommended: {SOURCE_EXCERPT_MIN_LENGTH} characters)')
            elif source_excerpt.isspace():
                warnings.append('source_excerpt contains only whitespace')
        else:
            warnings.append('source_excerpt is missing - traceability may be reduced')
        
        # 8. Validate rule type (if present)
        rule_type = rule_data.get('rule_type')
        if rule_type and rule_type not in VALID_RULE_TYPES:
            errors.append(f'Invalid rule_type "{rule_type}". Must be one of: {", ".join(VALID_RULE_TYPES)}')
        
        if errors:
            return {
                'valid': False,
                'error': '; '.join(errors),
                'warnings': warnings if warnings else None
            }
        
        return {
            'valid': True,
            'warnings': warnings if warnings else None
        }
    
    @staticmethod
    def _validate_requirement_code_format(code: str) -> bool:
        """
        Validate requirement code follows naming convention.
        
        Convention: UPPERCASE_WITH_UNDERSCORES, alphanumeric and underscores only.
        
        Args:
            code: Requirement code to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not code:
            return False
        
        # Check if it's uppercase
        if code != code.upper():
            return False
        
        # Check if it contains only alphanumeric characters and underscores
        if not re.match(r'^[A-Z0-9_]+$', code):
            return False
        
        # Check it doesn't start or end with underscore
        if code.startswith('_') or code.endswith('_'):
            return False
        
        # Check it doesn't have consecutive underscores
        if '__' in code:
            return False
        
        return True
    
    @staticmethod
    def validate_json_logic_comprehensive(condition_expression: Dict) -> Tuple[bool, Optional[str], List[str]]:
        """
        Comprehensive JSON Logic validation with detailed error reporting.
        
        Args:
            condition_expression: JSON Logic expression dictionary
            
        Returns:
            Tuple of (is_valid, error_message, warnings)
        """
        warnings = []
        
        # Basic validation
        is_valid, error = validate_json_logic(condition_expression)
        if not is_valid:
            return False, error, warnings
        
        # Additional checks
        # 1. Check for empty expressions
        if not condition_expression:
            return False, "Expression is empty", warnings
        
        # 2. Check for common issues
        expression_str = json.dumps(condition_expression)
        
        # Check for potential issues with variable names
        if '"var"' in expression_str:
            # Extract variable names and check for issues
            var_pattern = r'"var"\s*:\s*"([^"]+)"'
            variables = re.findall(var_pattern, expression_str)
            for var in variables:
                if not var or var.strip() != var:
                    warnings.append(f'Variable name "{var}" has leading/trailing whitespace')
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                    warnings.append(f'Variable name "{var}" may not be valid (should be alphanumeric with underscores)')
        
        # 3. Check for nested depth (too deep might indicate issues)
        depth = RuleValidator._calculate_expression_depth(condition_expression)
        if depth > 10:
            warnings.append(f'Expression depth is {depth} - may be too complex')
        
        return True, None, warnings
    
    @staticmethod
    def _calculate_expression_depth(expression: Dict, current_depth: int = 0) -> int:
        """Calculate the maximum nesting depth of a JSON Logic expression."""
        if not isinstance(expression, dict):
            return current_depth
        
        max_depth = current_depth
        for value in expression.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        depth = RuleValidator._calculate_expression_depth(item, current_depth + 1)
                        max_depth = max(max_depth, depth)
            elif isinstance(value, dict):
                depth = RuleValidator._calculate_expression_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
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
    
    @staticmethod
    def validate_rule_completeness(rule_data: Dict) -> Dict:
        """
        Validate that a rule has all necessary information for production use.
        
        This is a more strict validation than validate_rule_data, checking
        for completeness and quality, not just basic requirements.
        
        Args:
            rule_data: Rule data dictionary
            
        Returns:
            Dict with 'complete' (bool), 'missing_fields' (list), 'quality_issues' (list)
        """
        missing_fields = []
        quality_issues = []
        
        # Check all required fields
        for field in REQUIRED_RULE_FIELDS:
            if field not in rule_data or not rule_data[field]:
                missing_fields.append(field)
        
        # Check recommended fields
        if not rule_data.get('visa_code') or rule_data.get('visa_code') == 'UNKNOWN':
            quality_issues.append('visa_code is missing or UNKNOWN')
        
        if not rule_data.get('source_excerpt'):
            quality_issues.append('source_excerpt is missing (reduces traceability)')
        
        # Check JSON Logic validity
        condition_expr = rule_data.get('condition_expression', {})
        if condition_expr:
            is_valid, error = validate_json_logic(condition_expr)
            if not is_valid:
                quality_issues.append(f'Invalid JSON Logic: {error}')
        
        # Check if requirement code is standard
        requirement_code = rule_data.get('requirement_code', '')
        if requirement_code and not is_standard_requirement_code(requirement_code):
            quality_issues.append(f'requirement_code "{requirement_code}" is not a standard code')
        
        return {
            'complete': len(missing_fields) == 0 and len(quality_issues) == 0,
            'missing_fields': missing_fields,
            'quality_issues': quality_issues
        }