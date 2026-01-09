"""
Backward compatibility wrapper for RuleParsingService.

This file maintains backward compatibility for existing imports.
All new code should import from: data_ingestion.services.rule_parsing
"""

# Re-export from the new modular structure
from .rule_parsing.service import RuleParsingService

__all__ = ['RuleParsingService']
