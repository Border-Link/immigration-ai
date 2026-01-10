"""
JSON Logic validation utilities.

Validates that extracted JSON Logic expressions are valid and can be evaluated.
"""

import logging
import json_logic
from typing import Dict, Tuple, Optional, Any

logger = logging.getLogger('django')


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
        return False, f"Invalid JSON Logic expression: {str(e)}"
    except Exception as e:
        logger.warning(f"Unexpected error validating JSON Logic: {e}")
        return False, f"Validation error: {str(e)}"


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
        logger.warning(f"Error extracting variables: {e}")
    
    return variables
