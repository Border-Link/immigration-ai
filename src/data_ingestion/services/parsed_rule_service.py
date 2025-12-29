import logging
from typing import Optional
from data_ingestion.models.parsed_rule import ParsedRule
from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector

logger = logging.getLogger('django')


class ParsedRuleService:
    """Service for ParsedRule business logic."""

    @staticmethod
    def get_all():
        """Get all parsed rules."""
        try:
            return ParsedRuleSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all parsed rules: {e}")
            return ParsedRule.objects.none()

    @staticmethod
    def get_by_status(status: str):
        """Get parsed rules by status."""
        try:
            return ParsedRuleSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching parsed rules by status {status}: {e}")
            return ParsedRule.objects.none()

    @staticmethod
    def get_by_visa_code(visa_code: str):
        """Get parsed rules by visa code."""
        try:
            return ParsedRuleSelector.get_by_visa_code(visa_code)
        except Exception as e:
            logger.error(f"Error fetching parsed rules for visa code {visa_code}: {e}")
            return ParsedRule.objects.none()

    @staticmethod
    def get_pending():
        """Get all pending parsed rules."""
        try:
            return ParsedRuleSelector.get_pending()
        except Exception as e:
            logger.error(f"Error fetching pending parsed rules: {e}")
            return ParsedRule.objects.none()

    @staticmethod
    def get_by_id(rule_id: str) -> Optional[ParsedRule]:
        """Get parsed rule by ID."""
        try:
            return ParsedRuleSelector.get_by_id(rule_id)
        except ParsedRule.DoesNotExist:
            logger.error(f"Parsed rule {rule_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching parsed rule {rule_id}: {e}")
            return None

    @staticmethod
    def update_status(rule_id: str, status: str) -> Optional[ParsedRule]:
        """Update parsed rule status."""
        try:
            parsed_rule = ParsedRuleSelector.get_by_id(rule_id)
            return ParsedRuleRepository.update_status(parsed_rule, status)
        except ParsedRule.DoesNotExist:
            logger.error(f"Parsed rule {rule_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating parsed rule {rule_id} status: {e}")
            return None

    @staticmethod
    def update_parsed_rule(rule_id: str, **fields) -> Optional[ParsedRule]:
        """Update parsed rule fields."""
        try:
            parsed_rule = ParsedRuleSelector.get_by_id(rule_id)
            return ParsedRuleRepository.update_parsed_rule(parsed_rule, **fields)
        except ParsedRule.DoesNotExist:
            logger.error(f"Parsed rule {rule_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating parsed rule {rule_id}: {e}")
            return None

