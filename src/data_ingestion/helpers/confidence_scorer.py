"""
Enhanced confidence scoring for extracted rules.

Provides multi-factor confidence scoring with support for ML-based scoring.
"""

import logging
import re
from typing import Dict, Optional, Any
from data_ingestion.helpers.requirement_codes import (
    is_standard_requirement_code,
    get_requirement_code_category
)
from data_ingestion.helpers.json_logic_validator import validate_json_logic
from data_ingestion.helpers.rule_parsing_constants import (
    BASE_CONFIDENCE_SCORE,
    NUMERIC_VALUE_MATCH_BONUS,
    STANDARD_CODE_BONUS,
    VALID_JSON_LOGIC_BONUS,
    MAX_CONFIDENCE_SCORE,
)

logger = logging.getLogger('django')


class EnhancedConfidenceScorer:
    """
    Enhanced confidence scorer with multiple factors and ML-ready architecture.
    
    Scoring factors:
    1. Base score (50%)
    2. Numeric value matching (20%)
    3. Standard requirement code (20%)
    4. Valid JSON Logic (10%)
    5. Source excerpt quality (10%)
    6. Jurisdiction-specific patterns (5%)
    7. Rule type consistency (5%)
    8. Text length adequacy (5%)
    """
    
    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        'base': 0.50,
        'numeric_match': 0.20,
        'standard_code': 0.20,
        'valid_json_logic': 0.10,
        'source_excerpt_quality': 0.10,
        'jurisdiction_patterns': 0.05,
        'rule_type_consistency': 0.05,
        'text_length_adequacy': 0.05,
    }
    
    @staticmethod
    def compute_confidence_score(
        rule_data: Dict,
        source_text: str,
        jurisdiction: Optional[str] = None,
        document_quality: Optional[float] = None
    ) -> float:
        """
        Compute enhanced confidence score for extracted rule.
        
        Args:
            rule_data: Rule data dictionary
            source_text: Original source text for validation
            jurisdiction: Jurisdiction code (for pattern matching)
            document_quality: Optional document quality score (0.0-1.0)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        scores = {}
        
        # 1. Base score
        scores['base'] = BASE_CONFIDENCE_SCORE
        
        # 2. Numeric value matching
        scores['numeric_match'] = EnhancedConfidenceScorer._score_numeric_matching(
            rule_data, source_text
        )
        
        # 3. Standard requirement code
        scores['standard_code'] = EnhancedConfidenceScorer._score_standard_code(rule_data)
        
        # 4. Valid JSON Logic
        scores['valid_json_logic'] = EnhancedConfidenceScorer._score_json_logic(rule_data)
        
        # 5. Source excerpt quality
        scores['source_excerpt_quality'] = EnhancedConfidenceScorer._score_source_excerpt(
            rule_data, source_text
        )
        
        # 6. Jurisdiction-specific patterns
        scores['jurisdiction_patterns'] = EnhancedConfidenceScorer._score_jurisdiction_patterns(
            rule_data, jurisdiction
        )
        
        # 7. Rule type consistency
        scores['rule_type_consistency'] = EnhancedConfidenceScorer._score_rule_type_consistency(
            rule_data
        )
        
        # 8. Text length adequacy
        scores['text_length_adequacy'] = EnhancedConfidenceScorer._score_text_length(
            source_text
        )
        
        # Apply document quality multiplier if provided
        quality_multiplier = document_quality if document_quality else 1.0
        
        # Calculate weighted score
        total_score = sum(
            scores[factor] * EnhancedConfidenceScorer.WEIGHTS[factor]
            for factor in scores
        ) * quality_multiplier
        
        # Cap at maximum
        final_score = min(total_score, MAX_CONFIDENCE_SCORE)
        
        logger.debug(
            f"Confidence scoring breakdown: {scores}, "
            f"weighted_total: {total_score:.3f}, final: {final_score:.3f}"
        )
        
        return final_score
    
    @staticmethod
    def _score_numeric_matching(rule_data: Dict, source_text: str) -> float:
        """Score based on numeric value matching."""
        condition_expr = rule_data.get('condition_expression', {})
        if not condition_expr:
            return 0.0
        
        import json
        condition_str = json.dumps(condition_expr)
        numeric_values = re.findall(r'\d+', condition_str)
        
        if not numeric_values:
            return 0.0
        
        # Check how many numeric values appear in source text
        matches = sum(1 for num in numeric_values if num in source_text)
        match_ratio = matches / len(numeric_values) if numeric_values else 0.0
        
        # Return bonus proportional to match ratio
        return NUMERIC_VALUE_MATCH_BONUS * match_ratio
    
    @staticmethod
    def _score_standard_code(rule_data: Dict) -> float:
        """Score based on standard requirement code."""
        requirement_code = rule_data.get('requirement_code', '')
        if is_standard_requirement_code(requirement_code):
            return STANDARD_CODE_BONUS
        return 0.0
    
    @staticmethod
    def _score_json_logic(rule_data: Dict) -> float:
        """Score based on JSON Logic validity."""
        condition_expr = rule_data.get('condition_expression', {})
        if not condition_expr:
            return 0.0
        
        is_valid, _ = validate_json_logic(condition_expr)
        if is_valid:
            return VALID_JSON_LOGIC_BONUS
        return 0.0
    
    @staticmethod
    def _score_source_excerpt(rule_data: Dict, source_text: str) -> float:
        """Score based on source excerpt quality."""
        source_excerpt = rule_data.get('source_excerpt', '').strip()
        if not source_excerpt:
            return 0.0
        
        # Check if excerpt appears in source text
        if source_excerpt.lower() in source_text.lower():
            # Bonus for longer, more detailed excerpts
            excerpt_length = len(source_excerpt)
            if excerpt_length > 100:
                return 0.10  # Full bonus for detailed excerpts
            elif excerpt_length > 50:
                return 0.05  # Half bonus for medium excerpts
            else:
                return 0.02  # Small bonus for short excerpts
        
        return 0.0
    
    @staticmethod
    def _score_jurisdiction_patterns(rule_data: Dict, jurisdiction: Optional[str]) -> float:
        """Score based on jurisdiction-specific patterns."""
        if not jurisdiction:
            return 0.0
        
        requirement_code = rule_data.get('requirement_code', '').upper()
        description = rule_data.get('description', '').lower()
        
        # Jurisdiction-specific patterns
        patterns = {
            'UK': ['pound', 'gbp', 'uk', 'british', 'home office'],
            'US': ['dollar', 'usd', 'uscis', 'united states'],
            'CA': ['canadian', 'cad', 'ircc', 'canada'],
            'AU': ['australian', 'aud', 'department of home affairs', 'australia'],
        }
        
        jurisdiction_patterns = patterns.get(jurisdiction.upper(), [])
        matches = sum(1 for pattern in jurisdiction_patterns if pattern in description)
        
        if matches > 0:
            return 0.05 * (matches / len(jurisdiction_patterns))
        
        return 0.0
    
    @staticmethod
    def _score_rule_type_consistency(rule_data: Dict) -> float:
        """Score based on rule type consistency with requirement code."""
        from data_ingestion.helpers.requirement_codes import get_requirement_code_category
        
        requirement_code = rule_data.get('requirement_code', '').upper()
        description = rule_data.get('description', '').lower()
        
        category = get_requirement_code_category(requirement_code)
        
        # Check if description matches category
        category_keywords = {
            'fee': ['fee', 'cost', 'charge', 'payment'],
            'document': ['document', 'certificate', 'proof', 'evidence'],
            'processing_time': ['time', 'day', 'week', 'month', 'process'],
            'eligibility': ['require', 'must', 'need', 'eligible', 'qualify'],
        }
        
        keywords = category_keywords.get(category, [])
        matches = sum(1 for keyword in keywords if keyword in description)
        
        if matches > 0:
            return 0.05 * (matches / max(len(keywords), 1))
        
        return 0.0
    
    @staticmethod
    def _score_text_length(source_text: str) -> float:
        """Score based on source text length adequacy."""
        text_length = len(source_text)
        
        # Optimal length range: 500-5000 characters
        if 500 <= text_length <= 5000:
            return 0.05  # Full bonus
        elif 200 <= text_length < 500 or 5000 < text_length <= 10000:
            return 0.03  # Partial bonus
        elif text_length < 200:
            return 0.01  # Small bonus (too short)
        else:
            return 0.02  # Small bonus (very long, might be noisy)
    
    @staticmethod
    def compute_ml_confidence_score(
        rule_data: Dict,
        source_text: str,
        ml_model: Optional[Any] = None
    ) -> float:
        """
        Compute confidence score using ML model (if available).
        
        This is a placeholder for future ML integration. For now, falls back
        to enhanced scoring.
        
        Args:
            rule_data: Rule data dictionary
            source_text: Original source text
            ml_model: Optional ML model (scikit-learn, etc.)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # If ML model is provided, use it
        if ml_model:
            try:
                # Extract features for ML model
                features = EnhancedConfidenceScorer._extract_features(rule_data, source_text)
                
                # Predict using ML model
                # ml_score = ml_model.predict_proba([features])[0][1]
                # return float(ml_score)
                
                # Placeholder - would use actual ML model here
                logger.debug("ML model provided but not yet implemented")
            except Exception as e:
                logger.warning(f"ML model prediction failed: {e}, falling back to enhanced scoring")
        
        # Fallback to enhanced scoring
        return EnhancedConfidenceScorer.compute_confidence_score(rule_data, source_text)
    
    @staticmethod
    def _extract_features(rule_data: Dict, source_text: str) -> Dict[str, Any]:
        """
        Extract features for ML model training/prediction.
        
        Args:
            rule_data: Rule data dictionary
            source_text: Source text
            
        Returns:
            Dictionary of feature values
        """
        import json
        
        condition_expr = rule_data.get('condition_expression', {})
        requirement_code = rule_data.get('requirement_code', '')
        description = rule_data.get('description', '')
        source_excerpt = rule_data.get('source_excerpt', '')
        
        # Extract numeric values
        condition_str = json.dumps(condition_expr) if condition_expr else ''
        numeric_values = re.findall(r'\d+', condition_str)
        
        features = {
            'requirement_code_length': len(requirement_code),
            'description_length': len(description),
            'source_excerpt_length': len(source_excerpt),
            'source_text_length': len(source_text),
            'numeric_values_count': len(numeric_values),
            'is_standard_code': 1 if is_standard_requirement_code(requirement_code) else 0,
            'has_json_logic': 1 if condition_expr else 0,
            'json_logic_complexity': len(str(condition_expr)),
            'numeric_match_ratio': sum(1 for n in numeric_values if n in source_text) / max(len(numeric_values), 1),
            'excerpt_in_source': 1 if source_excerpt.lower() in source_text.lower() else 0,
        }
        
        return features


def compute_confidence_score(
    rule_data: Dict,
    source_text: str,
    jurisdiction: Optional[str] = None,
    document_quality: Optional[float] = None,
    use_ml: bool = False,
    ml_model: Optional[Any] = None
) -> float:
    """
    Convenience function to compute confidence score.
    
    Args:
        rule_data: Rule data dictionary
        source_text: Source text
        jurisdiction: Jurisdiction code
        document_quality: Document quality score
        use_ml: Whether to use ML model
        ml_model: Optional ML model
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    if use_ml and ml_model:
        return EnhancedConfidenceScorer.compute_ml_confidence_score(
            rule_data, source_text, ml_model
        )
    else:
        return EnhancedConfidenceScorer.compute_confidence_score(
            rule_data, source_text, jurisdiction, document_quality
        )
