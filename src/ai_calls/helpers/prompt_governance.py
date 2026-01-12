"""
Prompt Governance Helper

Manages prompt storage policy:
- Hash stored by default (privacy)
- Full prompt only when guardrails triggered or admin requested
"""
import hashlib
from typing import Optional


def compute_prompt_hash(prompt_text: str) -> str:
    """Compute SHA-256 hash of prompt for audit trail."""
    return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()


def should_store_full_prompt(guardrails_triggered: bool, admin_requested: bool = False) -> bool:
    """
    Determine if full prompt should be stored.
    
    Full prompt is stored when:
    - Guardrails are triggered (for compliance review)
    - Admin explicitly requests it (for debugging)
    """
    return guardrails_triggered or admin_requested
