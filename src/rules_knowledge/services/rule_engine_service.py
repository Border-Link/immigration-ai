"""
Rule Engine Service

A stateless, scalable service for evaluating immigration eligibility rules
using JSON Logic expressions. Designed to work across multiple jurisdictions
(UK, US, Canada, etc.) through rule versioning.

This service follows the design pattern from implementation.md Section 6.2.
"""
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
from django.utils import timezone
from django.db.models import Q
from main_system.utils import json_logic
from rules_knowledge.helpers.metrics import (
    rule_engine_evaluations_total,
    rule_engine_evaluation_duration_seconds,
    rule_engine_requirements_evaluated
)

from immigration_cases.models.case import Case
from immigration_cases.selectors.case_fact_selector import CaseFactSelector
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.visa_requirement import VisaRequirement
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.visa_requirement_selector import VisaRequirementSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector

logger = logging.getLogger('django')


class RuleEngineEvaluationResult:
    """Structured result from rule engine evaluation."""
    
    def __init__(self):
        self.outcome: str = 'unlikely'  # likely, possible, unlikely
        self.confidence: float = 0.0  # 0.0 to 1.0
        self.requirements_passed: int = 0
        self.requirements_total: int = 0
        self.requirements_failed: int = 0
        self.requirements_with_missing_facts: int = 0
        self.requirements_with_errors: int = 0
        self.requirement_details: List[Dict[str, Any]] = []
        self.missing_requirements: List[Dict[str, Any]] = []
        self.missing_facts: List[str] = []
        self.rule_version_id: Optional[str] = None
        self.rule_effective_from: Optional[datetime] = None
        self.evaluation_date: Optional[datetime] = None
        self.warnings: List[str] = []  # Additional warnings/notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'outcome': self.outcome,
            'confidence': round(self.confidence, 2),
            'requirements_passed': self.requirements_passed,
            'requirements_total': self.requirements_total,
            'requirements_failed': self.requirements_failed,
            'requirements_with_missing_facts': self.requirements_with_missing_facts,
            'requirements_with_errors': self.requirements_with_errors,
            'requirement_details': self.requirement_details,
            'missing_requirements': self.missing_requirements,
            'missing_facts': list(set(self.missing_facts)),  # Unique missing facts
            'rule_version_id': str(self.rule_version_id) if self.rule_version_id else None,
            'rule_effective_from': self.rule_effective_from.isoformat() if self.rule_effective_from else None,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'warnings': self.warnings,
        }


class RuleEngineService:
    """
    Stateless rule engine service for evaluating eligibility requirements.
    
    This service is jurisdiction-agnostic and works with any immigration system
    (UK, US, Canada, etc.) through rule versioning. It evaluates JSON Logic
    expressions against case facts to determine eligibility.
    
    Design Principles:
    - Stateless: All methods are static, no instance state
    - Scalable: Can be horizontally scaled across multiple instances
    - Jurisdiction-agnostic: Works with any jurisdiction through rule versions
    - Error-resilient: Handles missing facts, invalid expressions gracefully
    """
    
    @staticmethod
    def load_case_facts(case_id: str) -> Dict[str, Any]:
        """
        Step 1: Load case facts and convert to dictionary.
        
        Requires: Case must have a completed payment before case facts can be loaded.
        This ensures only paid cases can have their facts evaluated.
        
        Args:
            case_id: UUID of the case
            
        Returns:
            Dictionary mapping fact_key -> fact_value
            Example: {"age": 29, "salary": 42000, "nationality": "NG", "has_sponsor": true}
            
        Raises:
            ValueError: If case not found or payment not completed
        """
        from immigration_cases.selectors.case_selector import CaseSelector
        from payments.helpers.payment_validator import PaymentValidator
        
        case = CaseSelector.get_by_id(case_id)
        if not case:
            raise ValueError(f"Case with ID '{case_id}' not found")
        
        # Validate payment requirement (defense in depth)
        is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="case facts loading")
        if not is_valid:
            logger.warning(f"Case facts loading blocked for case {case_id}: {error}")
            raise ValueError(error)
        
        # Get all facts for the case, ordered by created_at DESC (most recent first)
        facts = CaseFactSelector.get_by_case(case)
        
        # Edge case: No facts for case
        if not facts.exists():
            logger.warning(f"Case {case_id} has no facts")
            return {}
        
        # Convert to dictionary, handling duplicates (latest wins)
        facts_dict = {}
        null_facts = []  # Track facts with null values
        
        for fact in facts:
            # Only keep the first occurrence (most recent due to DESC ordering)
            if fact.fact_key not in facts_dict:
                # Edge case: Handle null/None fact values
                if fact.fact_value is None:
                    null_facts.append(fact.fact_key)
                    logger.debug(f"Fact {fact.fact_key} has null value for case {case_id}")
                    # Store None anyway, JSON Logic can handle it
                    facts_dict[fact.fact_key] = None
                else:
                    facts_dict[fact.fact_key] = fact.fact_value
        
        if null_facts:
            logger.debug(f"Case {case_id} has {len(null_facts)} facts with null values: {null_facts}")
        
        logger.debug(f"Loaded {len(facts_dict)} unique facts for case {case_id}")
        return facts_dict
    
    @staticmethod
    def load_active_rule_version(visa_type_id: str, evaluation_date: Optional[datetime] = None) -> Optional[VisaRuleVersion]:
        """
        Step 2: Load active rule version for a visa type by effective date.
        
        Args:
            visa_type_id: UUID of the visa type
            evaluation_date: Date to evaluate against (defaults to now)
            
        Returns:
            Active VisaRuleVersion or None if not found
            
        Raises:
            ValueError: If visa type not found
        """
        if evaluation_date is None:
            evaluation_date = timezone.now()
        
        visa_type = VisaTypeSelector.get_by_id(visa_type_id)
        if not visa_type:
            raise ValueError(f"Visa type with ID '{visa_type_id}' not found")
        
        # Edge case: Check if visa type is active (if there's an is_active field)
        # Note: This assumes visa types might have an is_active field
        # If not, this check can be removed
        if hasattr(visa_type, 'is_active') and not visa_type.is_active:
            logger.warning(f"Visa type {visa_type_id} is not active")
            # Still proceed, but log warning
        
        # Query for active rule version
        # Active means: effective_from <= evaluation_date AND (effective_to IS NULL OR effective_to >= evaluation_date)
        # AND is_published = True
        active_versions = VisaRuleVersion.objects.select_related(
            'visa_type',
            'source_document_version'
        ).filter(
            visa_type=visa_type,
            is_published=True,
            effective_from__lte=evaluation_date
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=evaluation_date)
        ).order_by('-effective_from')
        
        rule_version = active_versions.first()
        
        if not rule_version:
            logger.warning(f"No active rule version found for visa type {visa_type_id} on {evaluation_date}")
            return None
        
        # Handle edge case: multiple active versions (shouldn't happen with proper versioning)
        version_count = active_versions.count()
        if version_count > 1:
            logger.warning(
                f"Multiple active rule versions found for visa type {visa_type_id} "
                f"({version_count} versions). Using most recent: {rule_version.id}"
            )
        
        logger.debug(f"Loaded active rule version {rule_version.id} for visa type {visa_type_id}")
        return rule_version
    
    @staticmethod
    def extract_variables_from_expression(expression: Dict[str, Any]) -> List[str]:
        """
        Extract variable names referenced in a JSON Logic expression.
        
        Args:
            expression: JSON Logic expression dictionary
            
        Returns:
            List of variable names (e.g., ["salary", "age"])
        """
        variables = []
        
        def traverse(obj):
            """Recursively traverse JSON Logic expression to find variables."""
            if isinstance(obj, dict):
                # Check for {"var": "variable_name"} pattern
                if "var" in obj:
                    var_name = obj["var"]
                    if isinstance(var_name, str) and var_name not in variables:
                        variables.append(var_name)
                # Recursively check all values
                for value in obj.values():
                    traverse(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)
        
        traverse(expression)
        return variables
    
    @staticmethod
    def validate_expression_structure(expression: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate that expression is a valid JSON Logic structure.
        
        Args:
            expression: Expression to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Edge case: Expression is None or empty
        if expression is None:
            return False, "Expression is None"
        
        if not isinstance(expression, (dict, list)):
            return False, f"Expression must be dict or list, got {type(expression).__name__}"
        
        # Edge case: Empty expression
        if isinstance(expression, dict) and len(expression) == 0:
            return False, "Expression is empty dictionary"
        
        if isinstance(expression, list) and len(expression) == 0:
            return False, "Expression is empty list"
        
        return True, None
    
    @staticmethod
    def normalize_fact_value(value: Any, expected_type: Optional[str] = None) -> Any:
        """
        Normalize fact value for JSON Logic evaluation.
        
        Handles type conversions and edge cases:
        - String numbers to numeric types
        - Date strings to dates
        - Boolean strings to booleans
        
        Args:
            value: Fact value to normalize
            expected_type: Optional expected type hint
            
        Returns:
            Normalized value
        """
        if value is None:
            return None
        
        # Edge case: String representations of numbers
        if isinstance(value, str) and expected_type in ('number', 'int', 'float'):
            try:
                # Try to convert string to number
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                pass  # Keep as string if conversion fails
        
        # Edge case: String representations of booleans
        if isinstance(value, str) and expected_type == 'boolean':
            lower_val = value.lower()
            if lower_val in ('true', '1', 'yes'):
                return True
            elif lower_val in ('false', '0', 'no'):
                return False
        
        return value
    
    @staticmethod
    def evaluate_expression(
        expression: Dict[str, Any],
        case_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a JSON Logic expression against case facts.
        
        This is a lower-level method for evaluating arbitrary JSON Logic expressions,
        useful for conditional logic in document requirements, etc.
        
        Args:
            expression: JSON Logic expression (dict or list)
            case_facts: Dictionary of case facts
            
        Returns:
            Dictionary with evaluation result:
            {
                "result": Any,  # The evaluation result (bool, number, etc.)
                "passed": bool,  # Boolean interpretation of result
                "missing_facts": List[str],  # Missing variables
                "error": Optional[str]  # Error message if evaluation failed
            }
        """
        result = {
            "result": None,
            "passed": False,
            "missing_facts": [],
            "error": None
        }
        
        try:
            # Edge case: Validate expression structure
            is_valid, error_msg = RuleEngineService.validate_expression_structure(expression)
            if not is_valid:
                result["error"] = error_msg
                logger.error(f"Invalid expression structure: {error_msg}")
                return result
            
            # Extract variables from expression
            required_variables = RuleEngineService.extract_variables_from_expression(expression)
            
            # Edge case: Expression has no variables (constant expression)
            if not required_variables:
                try:
                    evaluation_result = json_logic.jsonLogic(expression, {})
                    result["result"] = evaluation_result
                    result["passed"] = bool(evaluation_result)
                    return result
                except Exception as e:
                    result["error"] = f"Constant expression evaluation failed: {str(e)}"
                    return result
            
            # Check for missing variables
            missing_vars = [var for var in required_variables if var not in case_facts]
            if missing_vars:
                result["missing_facts"] = missing_vars
                logger.debug(f"Cannot evaluate expression: missing facts: {missing_vars}")
                return result
            
            # Prepare facts for JSON Logic (only include variables used in expression)
            facts_for_evaluation = {}
            for var in required_variables:
                fact_value = case_facts[var]
                normalized_value = RuleEngineService.normalize_fact_value(fact_value)
                facts_for_evaluation[var] = normalized_value
            
            # Evaluate JSON Logic expression
            try:
                evaluation_result = json_logic.jsonLogic(expression, facts_for_evaluation)
                
                # Edge case: Handle None result
                if evaluation_result is None:
                    result["result"] = None
                    result["passed"] = False
                    return result
                
                # Convert to boolean for pass/fail
                if isinstance(evaluation_result, bool):
                    result["passed"] = evaluation_result
                elif isinstance(evaluation_result, (int, float)):
                    import math
                    if math.isnan(evaluation_result) or math.isinf(evaluation_result):
                        result["error"] = f"Expression evaluated to {evaluation_result}"
                        return result
                    result["passed"] = bool(evaluation_result)
                else:
                    result["passed"] = bool(evaluation_result)
                
                result["result"] = evaluation_result
                return result
                
            except Exception as e:
                result["error"] = f"Expression evaluation failed: {str(e)}"
                logger.error(f"Error evaluating expression: {e}", exc_info=True)
                return result
                
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error in expression evaluation: {e}", exc_info=True)
            return result
    
    @staticmethod
    def evaluate_requirement(
        requirement: VisaRequirement,
        case_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 3: Evaluate a single requirement against case facts.
        
        Args:
            requirement: VisaRequirement to evaluate
            case_facts: Dictionary of case facts
            
        Returns:
            Dictionary with evaluation result:
            {
                "requirement_id": str,
                "requirement_code": str,
                "passed": bool,
                "missing_facts": List[str],
                "evaluation_details": Dict,
                "error": Optional[str]
            }
        """
        result = {
            "requirement_id": str(requirement.id),
            "requirement_code": requirement.requirement_code,
            "description": requirement.description,
            "rule_type": requirement.rule_type,
            "is_mandatory": requirement.is_mandatory,
            "passed": False,
            "missing_facts": [],
            "evaluation_details": {
                "expression": requirement.condition_expression,
                "facts_used": {},
                "result": None
            },
            "error": None
        }
        
        try:
            # Edge case: Validate expression structure
            is_valid, error_msg = RuleEngineService.validate_expression_structure(
                requirement.condition_expression
            )
            if not is_valid:
                result["error"] = error_msg
                result["evaluation_details"]["result"] = "invalid_structure"
                logger.error(
                    f"Invalid expression structure for requirement {requirement.requirement_code}: {error_msg}"
                )
                return result
            
            # Extract variables from expression
            required_variables = RuleEngineService.extract_variables_from_expression(
                requirement.condition_expression
            )
            
            # Edge case: Expression has no variables (constant expression)
            if not required_variables:
                logger.debug(
                    f"Requirement {requirement.requirement_code} has no variables in expression"
                )
                # Evaluate as constant expression
                try:
                    evaluation_result = json_logic.jsonLogic(
                        requirement.condition_expression,
                        {}
                    )
                    result["passed"] = bool(evaluation_result)
                    result["evaluation_details"]["result"] = evaluation_result
                    result["evaluation_details"]["facts_used"] = {}
                    return result
                except Exception as e:
                    result["error"] = f"Constant expression evaluation failed: {str(e)}"
                    result["evaluation_details"]["result"] = "error"
                    return result
            
            # Check for missing variables
            missing_vars = [var for var in required_variables if var not in case_facts]
            if missing_vars:
                result["missing_facts"] = missing_vars
                result["evaluation_details"]["result"] = "missing_facts"
                logger.debug(
                    f"Requirement {requirement.requirement_code} cannot be evaluated: "
                    f"missing facts: {missing_vars}"
                )
                return result
            
            # Prepare facts for JSON Logic (only include variables used in expression)
            facts_for_evaluation = {}
            for var in required_variables:
                fact_value = case_facts[var]
                # Edge case: Normalize fact values (handle type mismatches)
                # Note: We don't know expected type, so we normalize common cases
                normalized_value = RuleEngineService.normalize_fact_value(fact_value)
                facts_for_evaluation[var] = normalized_value
            
            result["evaluation_details"]["facts_used"] = facts_for_evaluation
            
            # Evaluate JSON Logic expression
            try:
                evaluation_result = json_logic.jsonLogic(
                    requirement.condition_expression,
                    facts_for_evaluation
                )
                
                # Edge case: Handle None result from JSON Logic
                if evaluation_result is None:
                    result["passed"] = False
                    result["evaluation_details"]["result"] = None
                    logger.debug(
                        f"Requirement {requirement.requirement_code} evaluated to None"
                    )
                    return result
                
                # JSON Logic returns boolean, number, or other value
                # Convert to boolean for pass/fail
                if isinstance(evaluation_result, bool):
                    result["passed"] = evaluation_result
                elif isinstance(evaluation_result, (int, float)):
                    # Edge case: Handle NaN and Infinity
                    import math
                    if math.isnan(evaluation_result) or math.isinf(evaluation_result):
                        result["error"] = f"Expression evaluated to {evaluation_result}"
                        result["evaluation_details"]["result"] = "invalid_result"
                        logger.error(
                            f"Requirement {requirement.requirement_code} evaluated to {evaluation_result}"
                        )
                        return result
                    # Non-zero numbers are truthy
                    result["passed"] = bool(evaluation_result)
                else:
                    # Other types: convert to boolean
                    result["passed"] = bool(evaluation_result)
                
                result["evaluation_details"]["result"] = evaluation_result
                
                logger.debug(
                    f"Requirement {requirement.requirement_code} evaluated: "
                    f"passed={result['passed']}, result={evaluation_result}"
                )
                
            except ZeroDivisionError as e:
                # Edge case: Division by zero in expression
                result["error"] = f"Division by zero in expression: {str(e)}"
                result["evaluation_details"]["result"] = "error"
                logger.error(
                    f"Division by zero in requirement {requirement.requirement_code}: {e}",
                    exc_info=True
                )
            except (TypeError, ValueError) as e:
                # Edge case: Type mismatch or value error
                result["error"] = f"Type or value error: {str(e)}"
                result["evaluation_details"]["result"] = "error"
                logger.error(
                    f"Type/value error in requirement {requirement.requirement_code}: {e}",
                    exc_info=True
                )
            except Exception as e:
                # Invalid expression or evaluation error
                result["error"] = str(e)
                result["evaluation_details"]["result"] = "error"
                logger.error(
                    f"Error evaluating requirement {requirement.requirement_code}: {e}",
                    exc_info=True
                )
                
        except Exception as e:
            # General error (e.g., invalid expression structure)
            result["error"] = f"Invalid expression: {str(e)}"
            logger.error(
                f"Error processing requirement {requirement.requirement_code}: {e}",
                exc_info=True
            )
        
        return result
    
    @staticmethod
    def evaluate_all_requirements(
        rule_version: VisaRuleVersion,
        case_facts: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all requirements for a rule version.
        
        Args:
            rule_version: VisaRuleVersion to evaluate
            case_facts: Dictionary of case facts
            
        Returns:
            List of evaluation results for each requirement
        """
        # Load all requirements for the rule version
        requirements = VisaRequirementSelector.get_by_rule_version(rule_version)
        
        # Edge case: No requirements for rule version
        if not requirements.exists():
            logger.warning(
                f"Rule version {rule_version.id} has no requirements"
            )
            return []
        
        evaluation_results = []
        for requirement in requirements:
            result = RuleEngineService.evaluate_requirement(requirement, case_facts)
            evaluation_results.append(result)
        
        logger.info(
            f"Evaluated {len(evaluation_results)} requirements for rule version {rule_version.id}"
        )
        return evaluation_results
    
    @staticmethod
    def aggregate_results(
        evaluation_results: List[Dict[str, Any]],
        rule_version: VisaRuleVersion
    ) -> RuleEngineEvaluationResult:
        """
        Step 4: Aggregate evaluation results and compute outcome.
        
        Args:
            evaluation_results: List of requirement evaluation results
            rule_version: The rule version that was evaluated
            
        Returns:
            RuleEngineEvaluationResult with aggregated outcome
        """
        result = RuleEngineEvaluationResult()
        result.rule_version_id = rule_version.id
        result.rule_effective_from = rule_version.effective_from
        result.evaluation_date = timezone.now()
        
        # Edge case: No evaluation results (no requirements)
        if not evaluation_results:
            result.warnings.append("No requirements found for this rule version")
            result.outcome = "unlikely"
            result.confidence = 0.0
            logger.warning(f"No evaluation results for rule version {rule_version.id}")
            return result
        
        # Count results
        total = len(evaluation_results)
        passed = sum(1 for eval_result in evaluation_results if eval_result.get("passed", False))
        failed = sum(1 for eval_result in evaluation_results if not eval_result.get("passed", False) and not eval_result.get("missing_facts") and not eval_result.get("error"))
        missing_facts_count = sum(1 for eval_result in evaluation_results if eval_result.get("missing_facts"))
        errors_count = sum(1 for eval_result in evaluation_results if eval_result.get("error"))
        
        result.requirements_total = total
        result.requirements_passed = passed
        result.requirements_failed = failed
        result.requirements_with_missing_facts = missing_facts_count
        result.requirements_with_errors = errors_count
        
        # Edge case: All requirements have errors
        if errors_count == total:
            result.warnings.append("All requirements have evaluation errors")
            result.outcome = "unlikely"
            result.confidence = 0.0
            logger.error(f"All requirements have errors for rule version {rule_version.id}")
            return result
        
        # Collect missing facts
        for eval_result in evaluation_results:
            if eval_result.get("missing_facts"):
                result.missing_facts.extend(eval_result["missing_facts"])
        
        # Collect requirement details
        result.requirement_details = evaluation_results
        
        # Collect missing requirements (for API response)
        for eval_result in evaluation_results:
            if eval_result.get("missing_facts") or eval_result.get("error"):
                result.missing_requirements.append({
                    "requirement_code": eval_result["requirement_code"],
                    "description": eval_result.get("description", ""),
                    "status": "missing_fact" if eval_result.get("missing_facts") else "error",
                    "missing_facts": eval_result.get("missing_facts", []),
                    "error": eval_result.get("error"),
                    "is_mandatory": eval_result.get("is_mandatory", True)
                })
        
        # Edge case: All requirements have missing facts
        if missing_facts_count == total:
            result.warnings.append("All requirements require missing facts")
            result.outcome = "unlikely"
            result.confidence = 0.0
            logger.warning(f"All requirements have missing facts for rule version {rule_version.id}")
            return result
        
        # Compute confidence score
        # Only count requirements that could be evaluated (not missing facts or errors)
        evaluable_count = total - missing_facts_count - errors_count
        
        if evaluable_count == 0:
            result.confidence = 0.0
        else:
            # Confidence = (passed requirements) / (total evaluable requirements)
            result.confidence = passed / evaluable_count
        
        # Edge case: Handle mandatory requirements separately
        # Count mandatory vs optional requirements
        mandatory_passed = sum(
            1 for eval_result in evaluation_results
            if eval_result.get("passed", False) and eval_result.get("is_mandatory", True)
        )
        mandatory_total = sum(
            1 for eval_result in evaluation_results
            if eval_result.get("is_mandatory", True) and not eval_result.get("missing_facts") and not eval_result.get("error")
        )
        
        # If any mandatory requirement failed, outcome should be unlikely
        if mandatory_total > 0:
            mandatory_failed = sum(
                1 for eval_result in evaluation_results
                if not eval_result.get("passed", False) and eval_result.get("is_mandatory", True) and not eval_result.get("missing_facts") and not eval_result.get("error")
            )
            if mandatory_failed > 0:
                result.warnings.append(f"{mandatory_failed} mandatory requirement(s) failed")
                # Override outcome if mandatory failed
                if result.confidence >= 0.8:
                    result.outcome = "possible"  # Downgrade from likely
                elif result.confidence >= 0.5:
                    result.outcome = "unlikely"  # Downgrade from possible
        
        # Map to outcome
        # If confidence >= 0.8 AND no missing facts AND no mandatory failures -> likely
        # If confidence >= 0.5 -> possible
        # Otherwise -> unlikely
        if result.confidence >= 0.8 and missing_facts_count == 0 and errors_count == 0:
            result.outcome = "likely"
        elif result.confidence >= 0.5:
            result.outcome = "possible"
        else:
            result.outcome = "unlikely"
        
        logger.info(
            f"Rule engine evaluation complete: outcome={result.outcome}, "
            f"confidence={result.confidence:.2f}, passed={passed}/{total}, "
            f"missing_facts={missing_facts_count}, errors={errors_count}"
        )
        
        return result
    
    @staticmethod
    def run_eligibility_evaluation(
        case_id: str,
        visa_type_id: str,
        evaluation_date: Optional[datetime] = None
    ) -> Optional[RuleEngineEvaluationResult]:
        """
        Main orchestration method: Run complete eligibility evaluation.
        
        Requires: Case must have a completed payment before eligibility can be evaluated.
        This ensures only paid cases can have their eligibility evaluated.
        
        This method combines all steps:
        1. Load case facts
        2. Load active rule version
        3. Evaluate all requirements
        4. Aggregate results
        
        Args:
            case_id: UUID of the case
            visa_type_id: UUID of the visa type to evaluate
            evaluation_date: Optional date to evaluate against (defaults to now)
            
        Returns:
            RuleEngineEvaluationResult or None if evaluation cannot be performed
            
        Raises:
            ValueError: If case or visa type not found, or payment not completed
        """
        from immigration_cases.selectors.case_selector import CaseSelector
        from payments.helpers.payment_validator import PaymentValidator
        
        # Validate payment requirement early (defense in depth)
        # This ensures payment validation even if called directly, not through EligibilityCheckService
        case = CaseSelector.get_by_id(case_id)
        if not case:
            raise ValueError(f"Case with ID '{case_id}' not found")
        
        is_valid, error = PaymentValidator.validate_case_has_payment(case, operation_name="eligibility evaluation")
        if not is_valid:
            logger.warning(f"Eligibility evaluation blocked for case {case_id}: {error}")
            raise ValueError(error)
        
        start_time = time.time()
        visa_type_code = 'unknown'
        
        try:
            # Get visa type code for metrics
            try:
                visa_type = VisaTypeSelector.get_by_id(visa_type_id)
                visa_type_code = visa_type.code if visa_type else 'unknown'
            except Exception:
                pass  # Use default if can't get visa type
            
            # Step 1: Load case facts
            case_facts = RuleEngineService.load_case_facts(case_id)
            
            # Edge case: Case has no facts
            if not case_facts:
                logger.warning(f"Case {case_id} has no facts - cannot evaluate eligibility")
                # Return a result indicating no facts
                result = RuleEngineEvaluationResult()
                result.warnings.append("Case has no facts")
                result.outcome = "unlikely"
                result.confidence = 0.0
                
                # Track metrics
                if rule_engine_evaluations_total:
                    rule_engine_evaluations_total.labels(visa_type=visa_type_code, outcome='unlikely').inc()
                if rule_engine_evaluation_duration_seconds:
                    rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type_code).observe(
                        time.time() - start_time
                    )
                
                return result
            
            # Step 2: Load active rule version
            rule_version = RuleEngineService.load_active_rule_version(visa_type_id, evaluation_date)
            if not rule_version:
                logger.warning(
                    f"No active rule version found for visa type {visa_type_id}. "
                    f"Cannot evaluate eligibility."
                )
                return None
            
            # Step 3: Evaluate all requirements
            evaluation_results = RuleEngineService.evaluate_all_requirements(
                rule_version,
                case_facts
            )
            
            # Edge case: No requirements to evaluate
            if not evaluation_results:
                result = RuleEngineEvaluationResult()
                result.rule_version_id = rule_version.id
                result.rule_effective_from = rule_version.effective_from
                result.evaluation_date = timezone.now()
                result.warnings.append("Rule version has no requirements")
                result.outcome = "unlikely"
                result.confidence = 0.0
                
                # Track metrics
                if rule_engine_evaluations_total:
                    rule_engine_evaluations_total.labels(visa_type=visa_type_code, outcome='unlikely').inc()
                if rule_engine_evaluation_duration_seconds:
                    rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type_code).observe(
                        time.time() - start_time
                    )
                
                return result
            
            # Step 4: Aggregate results
            result = RuleEngineService.aggregate_results(evaluation_results, rule_version)
            
            # Track metrics
            duration = time.time() - start_time
            if rule_engine_evaluations_total:
                rule_engine_evaluations_total.labels(visa_type=visa_type_code, outcome=result.outcome).inc()
            if rule_engine_evaluation_duration_seconds:
                rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type_code).observe(duration)
            if rule_engine_requirements_evaluated:
                rule_engine_requirements_evaluated.labels(visa_type=visa_type_code).observe(
                    result.requirements_total
                )
            
            return result
            
        except ValueError as ve:
            logger.error(f"Validation error in eligibility evaluation: {ve}")
            # Track error metrics
            if rule_engine_evaluations_total:
                rule_engine_evaluations_total.labels(visa_type=visa_type_code, outcome='error').inc()
            if rule_engine_evaluation_duration_seconds:
                rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type_code).observe(
                    time.time() - start_time
                )
            raise
        except Exception as e:
            logger.error(
                f"Error running eligibility evaluation for case {case_id}, "
                f"visa type {visa_type_id}: {e}",
                exc_info=True
            )
            # Track error metrics
            if rule_engine_evaluations_total:
                rule_engine_evaluations_total.labels(visa_type=visa_type_code, outcome='error').inc()
            if rule_engine_evaluation_duration_seconds:
                rule_engine_evaluation_duration_seconds.labels(visa_type=visa_type_code).observe(
                    time.time() - start_time
                )
            return None
