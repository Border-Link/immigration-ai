"""
Rule scoring and SLA calculation utilities.

Handles confidence scoring and SLA deadline calculation.
"""

import logging
from typing import Dict, Optional
from django.utils import timezone
from datetime import timedelta
from data_ingestion.helpers.confidence_scorer import compute_confidence_score as compute_enhanced_confidence_score
from data_ingestion.helpers.rule_parsing_constants import (
    DEFAULT_SLA_DAYS,
    URGENT_SLA_DAYS,
    HIGH_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger('django')


class RuleScorer:
    """Handles confidence scoring and SLA calculations."""
    
    @staticmethod
    def compute_confidence_score(
        rule_data: Dict,
        source_text: str,
        jurisdiction: Optional[str] = None
    ) -> float:
        """
        Compute enhanced confidence score for extracted rule.
        
        Uses multi-factor scoring with support for ML-based scoring.
        
        Args:
            rule_data: Rule data dictionary
            source_text: Original source text for validation
            jurisdiction: Optional jurisdiction code for pattern matching
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Use enhanced confidence scorer
        return compute_enhanced_confidence_score(
            rule_data=rule_data,
            source_text=source_text,
            jurisdiction=jurisdiction,
            use_ml=False  # Can be enabled when ML model is available
        )
    
    @staticmethod
    def calculate_sla_deadline(confidence_score: float) -> timezone.datetime:
        """
        Calculate SLA deadline based on confidence score.
        
        Args:
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            Datetime for SLA deadline
        """
        if confidence_score >= HIGH_CONFIDENCE_THRESHOLD:
            days = URGENT_SLA_DAYS
        else:
            days = DEFAULT_SLA_DAYS
        
        return timezone.now() + timedelta(days=days)
