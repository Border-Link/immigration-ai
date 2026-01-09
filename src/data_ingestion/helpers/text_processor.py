"""
Text processing utilities for rule parsing.

Handles encoding normalization, validation, preprocessing, and PII redaction.
"""

import logging
import unicodedata
from typing import Optional, Tuple, Dict
from data_ingestion.helpers.pii_detector import redact_pii_from_text

logger = logging.getLogger('django')


def normalize_text_encoding(text: str) -> str:
    """
    Normalize text encoding and remove problematic characters.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    try:
        # Normalize unicode (NFD -> NFC)
        normalized = unicodedata.normalize('NFC', text)
        
        # Remove control characters except newlines and tabs
        cleaned = ''.join(
            char for char in normalized
            if unicodedata.category(char)[0] != 'C' or char in ['\n', '\t', '\r']
        )
        
        return cleaned
        
    except Exception as e:
        logger.warning(f"Error normalizing text encoding: {e}")
        # Fallback: try to decode and re-encode
        try:
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            return text


def validate_text_for_parsing(text: str, min_length: int = 50) -> tuple[bool, Optional[str]]:
    """
    Validate text is suitable for parsing.
    
    Args:
        text: Text to validate
        min_length: Minimum required length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Text is empty"
    
    if not isinstance(text, str):
        return False, "Text must be a string"
    
    # Normalize encoding
    normalized = normalize_text_encoding(text)
    
    if len(normalized.strip()) < min_length:
        return False, f"Text too short (minimum {min_length} characters required)"
    
    # Check for reasonable content (not just whitespace or special chars)
    alphanumeric_chars = sum(1 for c in normalized if c.isalnum())
    if alphanumeric_chars < min_length * 0.5:  # At least 50% alphanumeric
        return False, "Text contains insufficient alphanumeric content"
    
    return True, None


def prepare_text_for_llm(text: str, redact_pii: bool = True) -> Tuple[str, Dict[str, any]]:
    """
    Prepare text for LLM processing with normalization and PII redaction.
    
    Args:
        text: Text to prepare
        redact_pii: Whether to redact PII (default: True)
        
    Returns:
        Tuple of (prepared_text, metadata_dict)
    """
    # Normalize encoding
    normalized = normalize_text_encoding(text)
    
    metadata = {
        'original_length': len(text),
        'normalized_length': len(normalized),
        'pii_redacted': False
    }
    
    # Redact PII if requested
    if redact_pii:
        redacted_text, pii_metadata = redact_pii_from_text(normalized)
        metadata.update(pii_metadata)
        return redacted_text, metadata
    
    return normalized, metadata
