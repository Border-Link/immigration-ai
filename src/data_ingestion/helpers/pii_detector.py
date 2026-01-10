"""
PII (Personally Identifiable Information) detection and redaction.

Detects and redacts PII from text before sending to LLM APIs.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger('django')


@dataclass
class PIIDetection:
    """Represents a detected PII item."""
    type: str  # email, phone, ssn, credit_card, etc.
    value: str  # Original value
    start: int  # Start position in text
    end: int  # End position in text
    confidence: float  # Detection confidence (0.0 to 1.0)


class PIIDetector:
    """
    Detects and redacts PII from text.
    
    Uses regex patterns for common PII types. Can be extended with
    more sophisticated libraries (presidio, spacy) if needed.
    """
    
    # Regex patterns for common PII types
    PATTERNS = {
        'email': re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        ),
        'phone_us': re.compile(
            r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        ),
        'phone_uk': re.compile(
            r'\b(?:\+44|0)?\s?(\d{4})\s?(\d{3})\s?(\d{3})\b'
        ),
        'ssn': re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        ),
        'credit_card': re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        ),
        'passport_number': re.compile(
            r'\b[A-Z]{1,2}\d{6,9}\b'
        ),
        'drivers_license': re.compile(
            r'\b[A-Z0-9]{8,12}\b'
        ),
        'ip_address': re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ),
        'date_of_birth': re.compile(
            r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b'
        ),
    }
    
    # Redaction replacements
    REDACTIONS = {
        'email': '[EMAIL_REDACTED]',
        'phone_us': '[PHONE_REDACTED]',
        'phone_uk': '[PHONE_REDACTED]',
        'ssn': '[SSN_REDACTED]',
        'credit_card': '[CARD_REDACTED]',
        'passport_number': '[PASSPORT_REDACTED]',
        'drivers_license': '[LICENSE_REDACTED]',
        'ip_address': '[IP_REDACTED]',
        'date_of_birth': '[DOB_REDACTED]',
    }
    
    @classmethod
    def detect(cls, text: str) -> List[PIIDetection]:
        """
        Detect PII in text.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of PIIDetection objects
        """
        detections = []
        
        for pii_type, pattern in cls.PATTERNS.items():
            for match in pattern.finditer(text):
                detections.append(PIIDetection(
                    type=pii_type,
                    value=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8  # Regex-based detection confidence
                ))
        
        # Sort by position
        detections.sort(key=lambda x: x.start)
        
        return detections
    
    @classmethod
    def redact(cls, text: str, detections: Optional[List[PIIDetection]] = None) -> Tuple[str, List[PIIDetection]]:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            detections: Optional pre-computed detections (if None, will detect)
            
        Returns:
            Tuple of (redacted_text, detections)
        """
        if detections is None:
            detections = cls.detect(text)
        
        if not detections:
            return text, []
        
        # Redact from end to start to preserve positions
        redacted_text = text
        for detection in reversed(detections):
            replacement = cls.REDACTIONS.get(detection.type, '[PII_REDACTED]')
            redacted_text = (
                redacted_text[:detection.start] +
                replacement +
                redacted_text[detection.end:]
            )
        
        logger.info(f"Redacted {len(detections)} PII items from text")
        
        return redacted_text, detections
    
    @classmethod
    def has_pii(cls, text: str) -> bool:
        """
        Check if text contains PII.
        
        Args:
            text: Text to check
            
        Returns:
            True if PII detected, False otherwise
        """
        detections = cls.detect(text)
        return len(detections) > 0
    
    @classmethod
    def get_pii_summary(cls, detections: List[PIIDetection]) -> Dict[str, int]:
        """
        Get summary of detected PII types.
        
        Args:
            detections: List of PII detections
            
        Returns:
            Dict mapping PII type to count
        """
        summary = {}
        for detection in detections:
            summary[detection.type] = summary.get(detection.type, 0) + 1
        return summary


def redact_pii_from_text(text: str) -> Tuple[str, Dict[str, any]]:
    """
    Convenience function to redact PII from text.
    
    Args:
        text: Text to redact
        
    Returns:
        Tuple of (redacted_text, metadata_dict)
    """
    detector = PIIDetector()
    detections = detector.detect(text)
    
    if not detections:
        return text, {
            'pii_detected': False,
            'pii_count': 0,
            'pii_types': {}
        }
    
    redacted_text, _ = detector.redact(text, detections)
    summary = detector.get_pii_summary(detections)
    
    return redacted_text, {
        'pii_detected': True,
        'pii_count': len(detections),
        'pii_types': summary,
        'redacted': True
    }
