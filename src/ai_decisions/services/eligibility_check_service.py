"""
Eligibility Check Service

Orchestration service that combines rule engine evaluation and AI reasoning
to produce final eligibility outcomes. This service implements the complete
eligibility check flow from implementation.md Section 6.4.

Design Principles:
- Stateless: All methods are static
- Resilient: Handles failures gracefully with fallbacks
- Traceable: All decisions are logged and stored
- Compliant: Follows OISC boundaries (decision support, not legal advice)
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.utils import timezone

from rules_knowledge.services.rule_engine_service import (
    RuleEngineService,
    RuleEngineEvaluationResult
)
from ai_decisions.services.ai_reasoning_service import AIReasoningService
from ai_decisions.services.eligibility_result_service import EligibilityResultService
from ai_decisions.services.ai_citation_service import AICitationService
from ai_decisions.models.eligibility_result import EligibilityResult
from immigration_cases.selectors.case_selector import CaseSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from human_reviews.services.review_service import ReviewService

logger = logging.getLogger('django')


class EligibilityCheckResult:
    """Structured result from eligibility check."""
    
    def __init__(self):
        self.success: bool = False
        self.case_id: Optional[str] = None
        self.visa_type_id: Optional[str] = None
        self.visa_code: Optional[str] = None
        self.outcome: str = 'unlikely'  # likely, possible, unlikely
        self.confidence: float = 0.0
        self.rule_engine_result: Optional[RuleEngineEvaluationResult] = None
        self.ai_reasoning_result: Optional[Dict[str, Any]] = None
        self.ai_reasoning_available: bool = False
        self.requires_human_review: bool = False
        self.conflict_detected: bool = False
        self.conflict_reason: Optional[str] = None
        self.eligibility_result_id: Optional[str] = None
        self.reasoning_summary: Optional[str] = None
        self.missing_facts: List[str] = []
        self.warnings: List[str] = []
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'success': self.success,
            'case_id': self.case_id,
            'visa_type_id': self.visa_type_id,
            'visa_code': self.visa_code,
            'outcome': self.outcome,
            'confidence': round(self.confidence, 2),
            'ai_reasoning_available': self.ai_reasoning_available,
            'requires_human_review': self.requires_human_review,
            'conflict_detected': self.conflict_detected,
            'conflict_reason': self.conflict_reason,
            'eligibility_result_id': self.eligibility_result_id,
            'reasoning_summary': self.reasoning_summary,
            'missing_facts': self.missing_facts,
            'warnings': self.warnings,
            'error': self.error,
        }


class EligibilityCheckService:
    """
    Orchestration service for eligibility checks.
    
    This service implements the complete eligibility check flow from
    implementation.md Section 6.4:
    1. Load prerequisites (case facts, rule version, visa type)
    2. Run rule engine evaluation
    3. Run AI reasoning (RAG)
    4. Handle AI service failures
    5. Combine outcomes
    6. Handle conflicts
    7. Store eligibility results
    8. Auto-escalate on low confidence
    """
    
    # Confidence threshold for auto-escalation
    LOW_CONFIDENCE_THRESHOLD = 0.6
    
    @staticmethod
    def run_eligibility_check(
        case_id: str,
        visa_type_id: str,
        evaluation_date: Optional[datetime] = None,
        enable_ai_reasoning: bool = True
    ) -> EligibilityCheckResult:
        """
        Main orchestration method: Run complete eligibility check.
        
        This method combines rule engine evaluation and AI reasoning to
        produce a final eligibility outcome.
        
        Args:
            case_id: UUID of the case
            visa_type_id: UUID of the visa type to evaluate
            evaluation_date: Optional date to evaluate against (defaults to now)
            enable_ai_reasoning: Whether to run AI reasoning (default: True)
            
        Returns:
            EligibilityCheckResult with complete evaluation results
            
        Raises:
            ValueError: If case or visa type not found
        """
        result = EligibilityCheckResult()
        result.case_id = case_id
        result.visa_type_id = visa_type_id
        
        try:
            # Step 1: Load prerequisites
            case = CaseSelector.get_by_id(case_id)
            if not case:
                result.error = f"Case {case_id} not found"
                logger.error(result.error)
                return result
            
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            if not visa_type:
                result.error = f"Visa type {visa_type_id} not found"
                logger.error(result.error)
                return result
            
            result.visa_code = visa_type.code
            
            # Load case facts
            case_facts = RuleEngineService.load_case_facts(case_id)
            if not case_facts:
                result.error = "Case has no facts"
                result.warnings.append("Case has no facts - cannot evaluate eligibility")
                logger.warning(f"Case {case_id} has no facts")
                return result
            
            # Step 2: Run rule engine evaluation
            logger.info(f"Running rule engine evaluation for case {case_id}, visa type {visa_type_id}")
            rule_engine_result = RuleEngineService.run_eligibility_evaluation(
                case_id=case_id,
                visa_type_id=visa_type_id,
                evaluation_date=evaluation_date
            )
            
            if not rule_engine_result:
                result.error = "Rule engine evaluation failed - no active rule version found"
                result.warnings.append("No active rule version found for this visa type")
                logger.warning(f"No active rule version for visa type {visa_type_id}")
                return result
            
            result.rule_engine_result = rule_engine_result
            result.warnings.extend(rule_engine_result.warnings)
            result.missing_facts = rule_engine_result.missing_facts
            
            # Step 3: Run AI reasoning (if enabled)
            ai_reasoning_result = None
            if enable_ai_reasoning:
                try:
                    logger.info(f"Running AI reasoning for case {case_id}, visa type {visa_type_id}")
                    ai_reasoning_result = AIReasoningService.run_ai_reasoning(
                        case_id=case_id,
                        case_facts=case_facts,
                        rule_results=rule_engine_result.to_dict(),
                        visa_type_id=visa_type_id,
                        visa_code=visa_type.code,
                        jurisdiction=case.jurisdiction if hasattr(case, 'jurisdiction') else None
                    )
                    
                    if ai_reasoning_result and ai_reasoning_result.get('success'):
                        result.ai_reasoning_available = True
                        result.ai_reasoning_result = ai_reasoning_result
                    else:
                        # AI reasoning failed, but we can continue with rule engine only
                        result.warnings.append("AI reasoning unavailable - using rule engine only")
                        logger.warning(f"AI reasoning failed for case {case_id}: {ai_reasoning_result.get('error') if ai_reasoning_result else 'Unknown error'}")
                        
                except Exception as e:
                    # AI service failure - fallback to rule engine only
                    result.warnings.append("AI reasoning service unavailable - using rule engine only")
                    logger.error(f"AI reasoning error for case {case_id}: {e}", exc_info=True)
            
            # Step 4: Combine outcomes
            combined_result = EligibilityCheckService._combine_outcomes(
                rule_engine_result=rule_engine_result,
                ai_reasoning_result=ai_reasoning_result,
                result=result
            )
            
            # Step 5: Store eligibility result
            eligibility_result = EligibilityCheckService._store_eligibility_result(
                case_id=case_id,
                visa_type_id=visa_type_id,
                rule_version_id=str(rule_engine_result.rule_version_id),
                outcome=combined_result['outcome'],
                confidence=combined_result['confidence'],
                reasoning_summary=combined_result['reasoning_summary'],
                missing_facts=result.missing_facts if result.missing_facts else None,
                ai_reasoning_log_id=ai_reasoning_result.get('reasoning_log_id') if ai_reasoning_result else None
            )
            
            if eligibility_result:
                result.eligibility_result_id = str(eligibility_result.id)
            
            # Step 6: Check for human review escalation
            if combined_result['requires_human_review']:
                EligibilityCheckService._escalate_to_human_review(
                    case_id=case_id,
                    reason=combined_result.get('escalation_reason', 'low_confidence_or_conflict')
                )
                result.requires_human_review = True
            
            result.success = True
            result.outcome = combined_result['outcome']
            result.confidence = combined_result['confidence']
            result.reasoning_summary = combined_result['reasoning_summary']
            
            logger.info(
                f"Eligibility check completed for case {case_id}, visa {visa_type_id}: "
                f"outcome={result.outcome}, confidence={result.confidence:.2f}, "
                f"requires_review={result.requires_human_review}"
            )
            
            return result
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"Error running eligibility check for case {case_id}: {e}", exc_info=True)
            return result
    
    @staticmethod
    def _combine_outcomes(
        rule_engine_result: RuleEngineEvaluationResult,
        ai_reasoning_result: Optional[Dict[str, Any]],
        result: EligibilityCheckResult
    ) -> Dict[str, Any]:
        """
        Combine rule engine and AI reasoning outcomes.
        
        Implements conflict detection and resolution logic from
        implementation.md Section 6.4, Step 5.
        
        Args:
            rule_engine_result: Rule engine evaluation result
            ai_reasoning_result: Optional AI reasoning result
            result: EligibilityCheckResult to update
            
        Returns:
            Dict with combined outcome, confidence, reasoning_summary, requires_human_review
        """
        # Start with rule engine outcome
        final_outcome = rule_engine_result.outcome  # likely, possible, unlikely
        final_confidence = rule_engine_result.confidence
        reasoning_summary = None
        requires_human_review = False
        escalation_reason = None
        
        # If AI reasoning is available, combine with rule engine
        if ai_reasoning_result and ai_reasoning_result.get('success'):
            ai_response = ai_reasoning_result.get('response', '')
            
            # Extract AI outcome from response (simple heuristic)
            # In production, this should parse structured JSON from LLM
            ai_outcome = EligibilityCheckService._extract_ai_outcome(ai_response)
            ai_confidence = EligibilityCheckService._extract_ai_confidence(ai_response, final_confidence)
            
            # Check for conflicts
            if EligibilityCheckService._is_conflict(rule_engine_result.outcome, ai_outcome):
                result.conflict_detected = True
                result.conflict_reason = f"Rule engine outcome ({rule_engine_result.outcome}) conflicts with AI outcome ({ai_outcome})"
                
                # Conservative resolution: use "possible" for conflicts
                final_outcome = 'possible'
                final_confidence = min(rule_engine_result.confidence, ai_confidence)
                requires_human_review = True
                escalation_reason = "rule_ai_conflict"
                reasoning_summary = (
                    f"Rule engine evaluation indicates {rule_engine_result.outcome} eligibility, "
                    f"while AI reasoning suggests {ai_outcome}. "
                    f"Human review recommended for accurate assessment."
                )
            else:
                # No conflict - use AI outcome (AI provides nuance)
                final_outcome = ai_outcome
                final_confidence = ai_confidence
                reasoning_summary = ai_response[:500]  # Truncate for summary
        else:
            # AI reasoning not available - use rule engine only
            reasoning_summary = (
                f"Rule engine evaluation: {rule_engine_result.requirements_passed} of "
                f"{rule_engine_result.requirements_total} requirements passed. "
                f"Confidence: {rule_engine_result.confidence:.0%}."
            )
        
        # Check for low confidence
        if final_confidence < EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD:
            requires_human_review = True
            if not escalation_reason:
                escalation_reason = "low_confidence"
            reasoning_summary = (
                f"{reasoning_summary or ''} "
                f"Confidence is below threshold ({final_confidence:.0%} < {EligibilityCheckService.LOW_CONFIDENCE_THRESHOLD:.0%}). "
                f"Human review recommended."
            )
        
        # Check for missing critical facts
        if result.missing_facts:
            requires_human_review = True
            if not escalation_reason:
                escalation_reason = "missing_critical_facts"
        
        return {
            'outcome': final_outcome,
            'confidence': final_confidence,
            'reasoning_summary': reasoning_summary,
            'requires_human_review': requires_human_review,
            'escalation_reason': escalation_reason
        }
    
    @staticmethod
    def _extract_ai_outcome(response_text: str) -> str:
        """
        Extract outcome (likely/possible/unlikely) from AI response.
        
        This is a simple heuristic. In production, the LLM should return
        structured JSON with explicit outcome field.
        
        Args:
            response_text: AI response text
            
        Returns:
            'likely', 'possible', or 'unlikely'
        """
        response_lower = response_text.lower()
        
        # Look for explicit outcome statements
        if 'likely' in response_lower and 'unlikely' not in response_lower:
            if 'not likely' in response_lower or 'unlikely' in response_lower:
                return 'unlikely'
            return 'likely'
        elif 'unlikely' in response_lower or 'not eligible' in response_lower:
            return 'unlikely'
        elif 'possible' in response_lower or 'may be eligible' in response_lower:
            return 'possible'
        else:
            # Default to possible if unclear
            return 'possible'
    
    @staticmethod
    def _extract_ai_confidence(response_text: str, fallback: float) -> float:
        """
        Extract confidence score from AI response.
        
        Args:
            response_text: AI response text
            fallback: Fallback confidence if not found
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        import re
        
        # Look for percentage patterns
        percentage_pattern = r'(\d+)%'
        matches = re.findall(percentage_pattern, response_text)
        if matches:
            try:
                percentage = int(matches[-1])  # Take last match
                return percentage / 100.0
            except ValueError:
                pass
        
        # Look for decimal patterns (0.0 to 1.0)
        decimal_pattern = r'0?\.\d+'
        matches = re.findall(decimal_pattern, response_text)
        if matches:
            try:
                confidence = float(matches[-1])
                if 0.0 <= confidence <= 1.0:
                    return confidence
            except ValueError:
                pass
        
        return fallback
    
    @staticmethod
    def _is_conflict(rule_outcome: str, ai_outcome: str) -> bool:
        """
        Check if rule engine and AI outcomes conflict.
        
        Conflict is defined as:
        - Rule says "unlikely" AND AI says "likely" (major conflict)
        - Rule says "likely" AND AI says "unlikely" (major conflict)
        
        Args:
            rule_outcome: Rule engine outcome
            ai_outcome: AI reasoning outcome
            
        Returns:
            True if conflict detected
        """
        # Major conflicts
        if rule_outcome == 'unlikely' and ai_outcome == 'likely':
            return True
        if rule_outcome == 'likely' and ai_outcome == 'unlikely':
            return True
        
        return False
    
    @staticmethod
    def _store_eligibility_result(
        case_id: str,
        visa_type_id: str,
        rule_version_id: str,
        outcome: str,
        confidence: float,
        reasoning_summary: Optional[str],
        missing_facts: Optional[List[str]],
        ai_reasoning_log_id: Optional[str]
    ) -> Optional[EligibilityResult]:
        """
        Store eligibility result in database.
        
        Maps implementation.md outcome values (likely/possible/unlikely) to
        model outcome choices. Note: Model currently uses different choices,
        so we map them appropriately.
        
        Args:
            case_id: Case ID
            visa_type_id: Visa type ID
            rule_version_id: Rule version ID
            outcome: Outcome (likely/possible/unlikely)
            confidence: Confidence score
            reasoning_summary: Summary text
            missing_facts: List of missing facts
            ai_reasoning_log_id: Optional AI reasoning log ID
            
        Returns:
            Created EligibilityResult or None
        """
        try:
            # Map implementation.md outcomes to model choices
            # Model uses: 'eligible', 'not_eligible', 'requires_review', 'missing_facts'
            # Implementation.md uses: 'likely', 'possible', 'unlikely'
            outcome_mapping = {
                'likely': 'eligible',
                'possible': 'requires_review',  # Possible cases need review
                'unlikely': 'not_eligible'
            }
            
            model_outcome = outcome_mapping.get(outcome, 'requires_review')
            
            # If missing facts, use 'missing_facts' outcome
            if missing_facts:
                model_outcome = 'missing_facts'
            
            eligibility_result = EligibilityResultService.create_eligibility_result(
                case_id=case_id,
                visa_type_id=visa_type_id,
                rule_version_id=rule_version_id,
                outcome=model_outcome,
                confidence=confidence,
                reasoning_summary=reasoning_summary,
                missing_facts={'missing_facts': missing_facts} if missing_facts else None
            )
            
            logger.info(
                f"Stored eligibility result {eligibility_result.id if eligibility_result else None} "
                f"for case {case_id}, visa {visa_type_id}"
            )
            
            return eligibility_result
            
        except Exception as e:
            logger.error(f"Error storing eligibility result: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _escalate_to_human_review(case_id: str, reason: str) -> Optional[Any]:
        """
        Create human review task for low confidence or conflicts.
        
        Implements auto-escalation from implementation.md Section 6.5.
        
        Args:
            case_id: Case ID
            reason: Reason for escalation (low_confidence, rule_ai_conflict, etc.)
            
        Returns:
            Created Review or None
        """
        try:
            logger.info(f"Escalating case {case_id} to human review: {reason}")
            
            review = ReviewService.create_review(
                case_id=case_id,
                auto_assign=True,
                assignment_strategy='workload'  # Use workload-based assignment
            )
            
            if review:
                logger.info(f"Created review {review.id} for case {case_id}")
            else:
                logger.warning(f"Failed to create review for case {case_id}")
            
            return review
            
        except Exception as e:
            logger.error(f"Error escalating case {case_id} to human review: {e}", exc_info=True)
            return None
