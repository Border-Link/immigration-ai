"""
Comprehensive dual-layer guardrails service for AI call validation.

Provides:
- Pre-prompt validation (user input)
- Post-response validation (AI output)
- Comprehensive pattern matching
- Context-aware validation
- Detailed violation tracking
- Sophisticated sanitization
"""
import logging
import re
from typing import Tuple, Optional, List, Dict, Any
from django.utils import timezone

from ai_calls.helpers.context_constants import RESTRICTED_TOPICS
from ai_calls.helpers.guardrails_patterns import (
    # Pre-prompt patterns
    COMPILED_LEGAL_ADVICE_PATTERNS,
    COMPILED_GUARANTEE_REQUEST_PATTERNS,
    COMPILED_OTHER_VISA_PATTERNS,
    COMPILED_FRAUD_PATTERNS,
    COMPILED_FINANCIAL_GUARANTEE_PATTERNS,
    # Post-response patterns
    COMPILED_LEGAL_ADVICE_LANGUAGE_PATTERNS,
    COMPILED_GUARANTEE_LANGUAGE_PATTERNS,
    COMPILED_PROACTIVE_PATTERNS,
    COMPILED_SAFETY_LANGUAGE_PATTERNS,
    COMPILED_OFF_SCOPE_PATTERNS,
    COMPILED_AUTHORITY_PATTERNS,
    # Helper functions
    normalize_text,
    check_patterns,
    find_matching_patterns,
    VIOLATION_CATEGORIES,
)

logger = logging.getLogger('django')


class GuardrailsService:
    """
    Comprehensive dual-layer guardrails service.
    
    Features:
    - Pre-prompt validation (user input)
    - Post-response validation (AI output)
    - Context-aware validation
    - Detailed violation tracking
    - Sophisticated sanitization
    - Performance optimized (compiled regex)
    """

    # Minimum response length requiring safety language
    MIN_RESPONSE_LENGTH_FOR_SAFETY_LANGUAGE = 50

    @staticmethod
    def validate_user_input_pre_prompt(
        user_text: str,
        context_bundle: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[List[str]]]:
        """
        Comprehensive PRE-PROMPT VALIDATION: Validate user input before sending to AI.
        
        Checks (in priority order):
        1. Fraud/evasion patterns (CRITICAL - immediate refuse)
        2. Restricted topics from context bundle
        3. Legal advice requests
        4. Guarantee requests
        5. Other visa/case discussion
        6. Financial guarantee requests
        
        Returns:
        - Tuple of (is_valid, error_message, action, violation_types)
        - Actions: 'allow', 'refuse', 'warn', 'escalate'
        - violation_types: List of detected violation types
        
        If 'refuse': Return refusal message immediately (no AI call)
        If 'warn': Allow but log warning
        If 'escalate': Allow but flag for human review
        """
        if not user_text or not user_text.strip():
            return False, "Empty input provided.", 'refuse', ['empty_input']
        
        user_text_normalized = normalize_text(user_text)
        violations = []
        violation_types = []
        
        # Priority 1: Check for fraud/evasion patterns (CRITICAL)
        if check_patterns(user_text, COMPILED_FRAUD_PATTERNS):
            violation_types.append('fraud')
            violations.append('fraud')
            logger.warning(f"Fraud pattern detected in user input: {user_text[:100]}")
            return (
                False,
                VIOLATION_CATEGORIES['fraud']['message'],
                'refuse',
                violation_types
            )
        
        # Priority 2: Check restricted topics from context bundle
        restricted_topics = context_bundle.get('restricted_topics', RESTRICTED_TOPICS)
        if restricted_topics:
            # Use efficient set-based matching
            user_words = set(user_text_normalized.split())
            for topic in restricted_topics:
                topic_words = set(topic.lower().split())
                # Check if any significant words from topic appear in user input
                if len(topic_words) > 0 and any(word in user_words for word in topic_words if len(word) > 3):
                    violation_types.append('restricted_topic')
                    violations.append(f"restricted_topic:{topic}")
                    logger.info(f"Restricted topic detected: {topic}")
                    return (
                        False,
                        f"Question is about restricted topic: {topic}. I can only discuss information related to your current immigration case.",
                        'refuse',
                        violation_types
                    )
        
        # Priority 3: Check for legal advice requests
        if check_patterns(user_text, COMPILED_LEGAL_ADVICE_PATTERNS):
            violation_types.append('legal_advice')
            violations.append('legal_advice')
            logger.info(f"Legal advice request detected")
            return (
                False,
                VIOLATION_CATEGORIES['legal_advice']['message'],
                'refuse',
                violation_types
            )
        
        # Priority 4: Check for guarantee requests
        if check_patterns(user_text, COMPILED_GUARANTEE_REQUEST_PATTERNS):
            violation_types.append('guarantee')
            violations.append('guarantee')
            logger.info(f"Guarantee request detected")
            return (
                False,
                VIOLATION_CATEGORIES['guarantee']['message'],
                'refuse',
                violation_types
            )
        
        # Priority 5: Check for other visa/case discussion
        if check_patterns(user_text, COMPILED_OTHER_VISA_PATTERNS):
            violation_types.append('other_visa')
            violations.append('other_visa')
            logger.info(f"Other visa/case discussion detected")
            return (
                False,
                VIOLATION_CATEGORIES['other_visa']['message'],
                'refuse',
                violation_types
            )
        
        # Priority 6: Check for financial guarantee requests
        if check_patterns(user_text, COMPILED_FINANCIAL_GUARANTEE_PATTERNS):
            violation_types.append('financial_guarantee')
            violations.append('financial_guarantee')
            logger.info(f"Financial guarantee request detected")
            return (
                False,
                VIOLATION_CATEGORIES['financial_guarantee']['message'],
                'refuse',
                violation_types
            )
        
        # All checks passed
        return True, None, 'allow', []

    @staticmethod
    def validate_ai_response_post_response(
        ai_text: str,
        context_bundle: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[List[str]]]:
        """
        Comprehensive POST-RESPONSE VALIDATION: Validate AI output before returning to user.
        
        Checks:
        1. Authority impersonation (CRITICAL)
        2. Legal advice language
        3. Guarantee language
        4. Proactive suggestions (reactive-only violation)
        5. Off-scope topics
        6. Safety language (required for longer responses)
        
        Returns:
        - Tuple of (is_valid, error_message, action, violation_types)
        - If invalid: Response should be sanitized or replaced
        - violation_types: List of detected violation types
        """
        if not ai_text or not ai_text.strip():
            return False, "Empty AI response.", 'sanitize', ['empty_response']
        
        ai_text_normalized = normalize_text(ai_text)
        violations = []
        violation_types = []
        
        # Priority 1: Check for authority impersonation (CRITICAL)
        if check_patterns(ai_text, COMPILED_AUTHORITY_PATTERNS):
            violation_types.append('authority_impersonation')
            violations.append('authority_impersonation')
            logger.error(f"Authority impersonation detected in AI response")
            return (
                False,
                VIOLATION_CATEGORIES['authority_impersonation']['message'],
                'sanitize',
                violation_types
            )
        
        # Priority 2: Check for legal advice language
        if check_patterns(ai_text, COMPILED_LEGAL_ADVICE_LANGUAGE_PATTERNS):
            violation_types.append('legal_advice')
            violations.append('legal_advice')
            logger.warning(f"Legal advice language detected in AI response")
        
        # Priority 3: Check for guarantee language
        if check_patterns(ai_text, COMPILED_GUARANTEE_LANGUAGE_PATTERNS):
            violation_types.append('guarantee')
            violations.append('guarantee')
            logger.warning(f"Guarantee language detected in AI response")
        
        # Priority 4: Check for proactive suggestions (reactive-only violation)
        if check_patterns(ai_text, COMPILED_PROACTIVE_PATTERNS):
            violation_types.append('proactive')
            violations.append('proactive')
            logger.info(f"Proactive suggestion detected in AI response")
        
        # Priority 5: Check for off-scope topics
        if check_patterns(ai_text, COMPILED_OFF_SCOPE_PATTERNS):
            violation_types.append('off_scope')
            violations.append('off_scope')
            logger.info(f"Off-scope topic detected in AI response")
        
        # Priority 6: Check for safety language (required for longer responses)
        has_safety_language = check_patterns(ai_text, COMPILED_SAFETY_LANGUAGE_PATTERNS)
        if not has_safety_language and len(ai_text.strip()) > GuardrailsService.MIN_RESPONSE_LENGTH_FOR_SAFETY_LANGUAGE:
            violation_types.append('missing_safety_language')
            violations.append('missing_safety_language')
            logger.info(f"Missing safety language in AI response (length: {len(ai_text)})")
        
        # Return validation result
        if violations:
            error_message = f"AI response contains violations: {', '.join(violation_types)}"
            return False, error_message, 'sanitize', violation_types
        
        return True, None, 'allow', []

    @staticmethod
    def enforce_reactive_only(ai_text: str) -> Tuple[bool, List[str]]:
        """
        Check if AI response violates reactive-only model.
        
        Detects:
        - Proactive questions
        - Unsolicited suggestions
        - AI-initiated topics
        
        Returns:
        - Tuple of (is_violated, matched_patterns)
        """
        if not ai_text:
            return False, []
        
        matched_patterns = find_matching_patterns(ai_text, COMPILED_PROACTIVE_PATTERNS)
        return len(matched_patterns) > 0, matched_patterns

    @staticmethod
    def generate_refusal_message(off_scope_topic: Optional[str] = None) -> str:
        """
        Generate polite refusal message for off-scope questions.
        
        Args:
            off_scope_topic: Optional specific topic that was off-scope
        """
        base_message = (
            "I can only discuss information related to your current immigration case. "
            "This is informational guidance based on your case details, not legal advice."
        )
        
        if off_scope_topic:
            return (
                f"{base_message} "
                f"For questions about {off_scope_topic}, please consult a qualified immigration adviser."
            )
        
        return (
            f"{base_message} "
            "For questions outside your case scope or requiring legal advice, "
            "please consult a qualified immigration adviser."
        )

    @staticmethod
    def generate_safety_language() -> str:
        """Generate safety language prefix for AI responses."""
        return "Based on your case information, "

    @staticmethod
    def sanitize_ai_response(ai_text: str, violations: List[str]) -> str:
        """
        Comprehensive sanitization of AI response that failed post-response validation.
        
        Sanitization steps:
        1. Remove problematic phrases
        2. Replace guarantee language with softer alternatives
        3. Remove proactive suggestions
        4. Add safety language if missing
        5. Ensure compliance with reactive-only model
        
        Args:
            ai_text: Original AI response
            violations: List of violation types detected
        
        Returns:
            Sanitized AI response
        """
        if not ai_text:
            return GuardrailsService.generate_safety_language() + "I cannot provide a response at this time."
        
        sanitized = ai_text
        
        # Remove guarantee language
        if 'guarantee' in violations:
            # Replace guarantee phrases with softer alternatives
            replacements = {
                'guaranteed': 'likely',
                'will definitely': 'appears to',
                'will absolutely': 'appears to',
                'certain to': 'likely to',
                'assured': 'likely',
                'for sure': 'likely',
                'no doubt': 'appears',
                'absolutely certain': 'appears likely',
                '100% guarantee': 'appears likely',
            }
            for old_phrase, new_phrase in replacements.items():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(old_phrase), re.IGNORECASE)
                sanitized = pattern.sub(new_phrase, sanitized)
        
        # Remove legal advice language
        if 'legal_advice' in violations:
            # Remove or soften legal obligation phrases
            legal_phrases = [
                r'\byou\s+must\b',
                r'\byou\s+are\s+required\s+by\s+law\b',
                r'\blegal\s+obligation\b',
                r'\blegally\s+bound\b',
            ]
            for phrase in legal_phrases:
                pattern = re.compile(phrase, re.IGNORECASE)
                sanitized = pattern.sub('you may need to', sanitized)
        
        # Remove proactive suggestions
        if 'proactive' in violations:
            # Remove sentences containing proactive patterns
            sentences = re.split(r'[.!?]+', sanitized)
            filtered_sentences = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                is_proactive = any(
                    pattern.search(sentence_lower)
                    for pattern in COMPILED_PROACTIVE_PATTERNS
                )
                if not is_proactive:
                    filtered_sentences.append(sentence)
            sanitized = '. '.join(filtered_sentences).strip()
            if sanitized and not sanitized.endswith(('.', '!', '?')):
                sanitized += '.'
        
        # Remove authority impersonation
        if 'authority_impersonation' in violations:
            authority_phrases = [
                r'\bi\s+am\s+an\s+immigration\s+officer\b',
                r'\bwe\s+are\s+the\s+government\b',
                r'\bofficial\s+decision\b',
            ]
            for phrase in authority_phrases:
                pattern = re.compile(phrase, re.IGNORECASE)
                sanitized = pattern.sub('', sanitized)
        
        # Add safety language if missing
        safety_prefix = GuardrailsService.generate_safety_language()
        if 'missing_safety_language' in violations or not any(
            pattern.search(sanitized.lower())
            for pattern in COMPILED_SAFETY_LANGUAGE_PATTERNS
        ):
            # Only add if not already present
            if not sanitized.lower().startswith(safety_prefix.lower()):
                sanitized = safety_prefix + sanitized
        
        # Clean up any double spaces or formatting issues
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Ensure response is not empty after sanitization
        if not sanitized or len(sanitized.strip()) < 10:
            sanitized = (
                safety_prefix +
                "I can provide information about your case, but I cannot provide specific guarantees or legal advice. "
                "Please consult a qualified immigration adviser for personalized guidance."
            )
        
        return sanitized

    @staticmethod
    def get_violation_severity(violation_type: str) -> str:
        """
        Get severity level for a violation type.
        
        Returns:
            'critical', 'high', 'medium', or 'low'
        """
        category = VIOLATION_CATEGORIES.get(violation_type, {})
        return category.get('severity', 'medium')

    @staticmethod
    def should_escalate(violation_types: List[str]) -> bool:
        """
        Determine if violations should be escalated to human review.
        
        Escalation criteria:
        - Critical severity violations
        - Multiple high severity violations
        - Fraud patterns detected
        
        Returns:
            True if should escalate
        """
        if not violation_types:
            return False
        
        critical_violations = ['fraud', 'authority_impersonation']
        high_violations = ['legal_advice', 'guarantee', 'financial_guarantee']
        
        # Escalate if any critical violation
        if any(v in critical_violations for v in violation_types):
            return True
        
        # Escalate if multiple high severity violations
        high_count = sum(1 for v in violation_types if v in high_violations)
        if high_count >= 2:
            return True
        
        return False

    @staticmethod
    def validate_context_bundle_for_guardrails(context_bundle: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that context bundle has required fields for guardrails.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not context_bundle:
            return False, "Context bundle is empty"
        
        required_fields = ['case_id', 'restricted_topics']
        missing_fields = [f for f in required_fields if f not in context_bundle]
        
        if missing_fields:
            return False, f"Context bundle missing required fields for guardrails: {', '.join(missing_fields)}"
        
        return True, None
