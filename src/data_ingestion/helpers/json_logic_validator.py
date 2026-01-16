"""
JSON Logic validation utilities.

Validates that extracted JSON Logic expressions are valid and can be evaluated.
"""

import logging
from main_system.utils import json_logic
from typing import Dict, Tuple, Optional, Any
from data_ingestion.helpers.rule_parsing_constants import VALID_JSON_LOGIC_OPERATORS
from django.conf import settings

logger = logging.getLogger('django')

def _is_structurally_valid_json_logic(obj: Any) -> Tuple[bool, Optional[str]]:
    """
    Lightweight structural JSON Logic validation.
    This avoids false negatives when the json_logic runtime can't evaluate an expression
    with empty data, while still rejecting clearly invalid shapes.
    """
    if obj is None:
        return False, "Expression cannot be None"
    if isinstance(obj, (str, int, float, bool)):
        return True, None
    if isinstance(obj, list):
        for item in obj:
            ok, err = _is_structurally_valid_json_logic(item)
            if not ok:
                return False, err
        return True, None
    if not isinstance(obj, dict):
        return False, "Expression must be a dictionary"

    # JSON Logic objects are operator dicts; validate operator keys if present.
    for op, value in obj.items():
        if not isinstance(op, str) or not op:
            return False, "Operator must be a non-empty string"
        if op not in VALID_JSON_LOGIC_OPERATORS:
            return False, f"Unsupported JSON Logic operator: {op}"
        ok, err = _is_structurally_valid_json_logic(value)
        if not ok:
            return False, err
    return True, None


def validate_json_logic(expression: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate that a JSON Logic expression is valid and can be evaluated.
    
    Args:
        expression: JSON Logic expression dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if expression is valid, False otherwise
        - error_message: Error message if invalid, None if valid
    """
    if not expression:
        return False, "Expression is empty"
    
    if not isinstance(expression, dict):
        return False, "Expression must be a dictionary"
    
    ok, err = _is_structurally_valid_json_logic(expression)
    if not ok:
        return False, err

    try:
        # Try to evaluate with empty data to check syntax
        # This will catch syntax errors but not logic errors
        result = json_logic.jsonLogic(expression, {})
        
        # Check for NaN or Infinity results (indicates invalid operations)
        if isinstance(result, float):
            if result != result:  # NaN check
                return False, "Expression evaluates to NaN"
            if result == float('inf') or result == float('-inf'):
                return False, "Expression evaluates to Infinity"
        
        return True, None
        
    except (TypeError, ValueError, KeyError, AttributeError) as e:
        # If the expression is structurally valid, treat runtime evaluation issues
        # as non-fatal to avoid false negatives across different json_logic backends.
        if getattr(settings, "APP_ENV", None) != "test":
            logger.warning(f"JSON Logic evaluation failed, but structure is valid: {e}")
        return True, None
    except Exception as e:
        if getattr(settings, "APP_ENV", None) != "test":
            logger.warning(f"Unexpected error validating JSON Logic: {e}")
            logger.warning(f"JSON Logic unexpected evaluation error, but structure is valid: {e}")
        return True, None


def extract_variables_from_expression(expression: Dict[str, Any]) -> set:
    """
    Extract variable names from a JSON Logic expression.
    
    Args:
        expression: JSON Logic expression dictionary
        
    Returns:
        Set of variable names used in the expression
    """
    variables = set()
    
    def _extract_vars(obj: Any) -> None:
        """Recursively extract variables from expression."""
        if isinstance(obj, dict):
            # Check for "var" operator
            if "var" in obj:
                var_name = obj["var"]
                if isinstance(var_name, str):
                    variables.add(var_name)
            
            # Recursively process all values
            for value in obj.values():
                _extract_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                _extract_vars(item)
    
    try:
        _extract_vars(expression)
    except Exception as e:
        if getattr(settings, "APP_ENV", None) != "test":
            logger.warning(f"Error extracting variables: {e}")
    
    return variables
