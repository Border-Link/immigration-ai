"""
Case Validator for Business Rules

Validates business rules for cases and case facts.
"""
from typing import Tuple, Optional
from django.core.exceptions import ValidationError


# Common fact keys that are allowed (can be extended)
ALLOWED_FACT_KEYS = {
    'salary', 'age', 'nationality', 'education_level', 'work_experience_years',
    'language_proficiency', 'spouse_included', 'dependents_count', 'job_offer',
    'sponsor', 'visa_type_preference', 'current_location', 'target_location',
    'previous_visa_refusals', 'criminal_record', 'health_conditions',
    'financial_savings', 'employment_status', 'marital_status'
}

# Fact value type validation
FACT_VALUE_TYPES = {
    'salary': (int, float),
    'age': int,
    'work_experience_years': int,
    'dependents_count': int,
    'spouse_included': bool,
    'job_offer': bool,
    'previous_visa_refusals': bool,
    'criminal_record': bool,
    'health_conditions': bool,
}


class CaseValidator:
    """Validator for case business rules."""
    
    @staticmethod
    def validate_fact_key(fact_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that fact key is allowed.
        
        Args:
            fact_key: The fact key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not fact_key or not isinstance(fact_key, str):
            return False, "Fact key must be a non-empty string"
        
        fact_key_lower = fact_key.lower().strip()
        
        # Allow any key for flexibility, but warn about unknown keys
        # In production, you might want to enforce strict whitelist
        if fact_key_lower not in {k.lower() for k in ALLOWED_FACT_KEYS}:
            # Log warning but allow (flexible design)
            pass
        
        return True, None
    
    @staticmethod
    def validate_fact_value(fact_key: str, fact_value) -> Tuple[bool, Optional[str]]:
        """
        Validate that fact value matches expected type for the fact key.
        
        Args:
            fact_key: The fact key
            fact_value: The fact value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if fact_value is None:
            return False, "Fact value cannot be None"
        
        fact_key_lower = fact_key.lower().strip()
        expected_type = FACT_VALUE_TYPES.get(fact_key_lower)
        
        if expected_type:
            if not isinstance(fact_value, expected_type):
                return False, (
                    f"Fact value for '{fact_key}' must be of type {expected_type.__name__}, "
                    f"got {type(fact_value).__name__}"
                )
        
        # Additional validation for specific keys
        if fact_key_lower == 'age' and isinstance(fact_value, int):
            if fact_value < 0 or fact_value > 150:
                return False, "Age must be between 0 and 150"
        
        if fact_key_lower == 'salary' and isinstance(fact_value, (int, float)):
            if fact_value < 0:
                return False, "Salary cannot be negative"
        
        if fact_key_lower == 'work_experience_years' and isinstance(fact_value, int):
            if fact_value < 0 or fact_value > 100:
                return False, "Work experience years must be between 0 and 100"
        
        return True, None
    
    @staticmethod
    def validate_case_prerequisites_for_status(case, new_status: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that case has prerequisites for status transition.
        
        Args:
            case: The case object
            new_status: The new status to transition to
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from immigration_cases.selectors.case_fact_selector import CaseFactSelector
        
        # Check prerequisites for 'evaluated' status
        if new_status == 'evaluated':
            facts = CaseFactSelector.get_by_case(case)
            if not facts.exists():
                return False, "Case must have at least one fact before being evaluated"
        
        # Check prerequisites for 'awaiting_review' status
        if new_status == 'awaiting_review':
            if case.status != 'evaluated':
                return False, "Case must be in 'evaluated' status before awaiting review"
        
        # Check prerequisites for 'reviewed' status
        if new_status == 'reviewed':
            if case.status not in ['awaiting_review', 'evaluated']:
                return False, "Case must be in 'awaiting_review' or 'evaluated' status before being reviewed"
        
        return True, None
