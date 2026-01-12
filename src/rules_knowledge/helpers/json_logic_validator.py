"""
JSON Logic Expression Validator

Validates JSON Logic expressions before saving to database.
"""
import logging
from typing import Tuple, Optional, Any, Dict
import json_logic

logger = logging.getLogger('django')


class JSONLogicValidator:
    """Validator for JSON Logic expressions."""
    
    # Valid JSON Logic operators
    VALID_OPERATORS = [
        'var', 'missing', 'missing_some', 'if', '==', '===', '!=', '!==',
        '!', '!!', 'or', 'and', '>', '>=', '<', '<=', '+', '-', '*', '/',
        '%', 'max', 'min', 'abs', 'cat', 'substr', 'in', 'merge', 'map',
        'filter', 'reduce', 'all', 'none', 'some', 'log', 'method'
    ]
    
    @staticmethod
    def validate_expression(expression: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON Logic expression structure and syntax.
        
        Args:
            expression: JSON Logic expression to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if expression is a dict (JSON Logic expressions are dicts)
            if not isinstance(expression, dict):
                return False, "Expression must be a dictionary/object"
            
            # Check if expression is empty
            if not expression:
                return False, "Expression cannot be empty"
            
            # Validate structure recursively (with node counting for complexity limits)
            is_valid, error = JSONLogicValidator._validate_structure(expression, depth=0, node_count=0)
            if not is_valid:
                return False, error
            
            # Test expression with sample data to catch syntax errors
            try:
                test_data = {}
                json_logic.jsonLogic(expression, test_data)
            except Exception as e:
                return False, f"Expression syntax error: {str(e)}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating JSON Logic expression: {e}", exc_info=True)
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def _validate_structure(expression: Any, depth: int = 0, node_count: int = 0) -> Tuple[bool, Optional[str]]:
        """
        Recursively validate JSON Logic expression structure.
        
        Security: Limits expression complexity to prevent DoS attacks.
        
        Args:
            expression: Expression to validate
            depth: Current recursion depth (to prevent infinite loops)
            node_count: Current node count (to limit expression size)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Security: Prevent infinite recursion
        MAX_DEPTH = 20
        if depth > MAX_DEPTH:
            return False, f"Expression too deeply nested (max depth: {MAX_DEPTH})"
        
        # Security: Limit total expression size to prevent DoS
        MAX_NODES = 1000
        if node_count > MAX_NODES:
            return False, f"Expression too complex (max nodes: {MAX_NODES})"
        
        # Increment node count for this node
        node_count += 1
        
        # If it's a dict, check if it's a valid JSON Logic operation
        if isinstance(expression, dict):
            if len(expression) == 0:
                return False, "Empty object in expression"
            
            # Check if it's a valid operator
            keys = list(expression.keys())
            if len(keys) == 1:
                operator = keys[0]
                value = expression[operator]
                
                # Check if operator is valid
                if operator not in JSONLogicValidator.VALID_OPERATORS:
                    return False, f"Invalid operator: '{operator}'. Valid operators: {', '.join(JSONLogicValidator.VALID_OPERATORS[:10])}..."
                
                # Recursively validate the value
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        for item in value:
                            is_valid, error = JSONLogicValidator._validate_structure(item, depth + 1, node_count)
                            if not is_valid:
                                return False, error
                    else:
                        is_valid, error = JSONLogicValidator._validate_structure(value, depth + 1, node_count)
                        if not is_valid:
                            return False, error
            else:
                # Multiple keys - might be valid for some operators, but generally invalid
                return False, f"Expression object has multiple keys: {keys}. JSON Logic expressions should have a single operator key."
        
        # If it's a list, validate each item
        elif isinstance(expression, list):
            for item in expression:
                is_valid, error = JSONLogicValidator._validate_structure(item, depth + 1, node_count)
                if not is_valid:
                    return False, error
        
        # Primitive types (str, int, float, bool, None) are valid
        elif not isinstance(expression, (str, int, float, bool, type(None))):
            return False, f"Invalid type in expression: {type(expression).__name__}"
        
        return True, None
    
    @staticmethod
    def validate_expression_with_sample_data(
        expression: Dict[str, Any],
        sample_data: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str], Optional[Any]]:
        """
        Validate expression and test with sample data.
        
        Args:
            expression: JSON Logic expression
            sample_data: Optional sample data to test with
            
        Returns:
            Tuple of (is_valid, error_message, test_result)
        """
        # First validate structure
        is_valid, error = JSONLogicValidator.validate_expression(expression)
        if not is_valid:
            return False, error, None
        
        # Test with sample data if provided
        if sample_data is not None:
            try:
                result = json_logic.jsonLogic(expression, sample_data)
                return True, None, result
            except Exception as e:
                return False, f"Expression evaluation error: {str(e)}", None
        
        return True, None, None
