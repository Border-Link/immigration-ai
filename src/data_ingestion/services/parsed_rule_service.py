import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from data_ingestion.models.parsed_rule import ParsedRule
from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "parsed_rules"


class ParsedRuleService:
    """Service for ParsedRule business logic."""

    @staticmethod
    @cache_result(timeout=300, keys=[], namespace=namespace, user_scope="global")  # 5 minutes - parsed rules change when new ones are parsed
    def get_all():
        """Get all parsed rules."""
        try:
            return ParsedRuleSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all parsed rules: {e}")
            return ParsedRuleSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['status'], namespace=namespace, user_scope="global")  # 5 minutes - cache by status
    def get_by_status(status: str):
        """Get parsed rules by status."""
        try:
            return ParsedRuleSelector.get_by_status(status)
        except Exception as e:
            logger.error(f"Error fetching parsed rules by status {status}: {e}")
            return ParsedRuleSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['visa_code'], namespace=namespace, user_scope="global")  # 5 minutes - cache by visa code
    def get_by_visa_code(visa_code: str):
        """Get parsed rules by visa code."""
        try:
            return ParsedRuleSelector.get_by_visa_code(visa_code)
        except Exception as e:
            logger.error(f"Error fetching parsed rules for visa code {visa_code}: {e}")
            return ParsedRuleSelector.get_none()

    @staticmethod
    @cache_result(timeout=180, keys=[], namespace=namespace, user_scope="global")  # 3 minutes - pending rules change frequently
    def get_pending():
        """Get all pending parsed rules."""
        try:
            return ParsedRuleSelector.get_pending()
        except Exception as e:
            logger.error(f"Error fetching pending parsed rules: {e}")
            return ParsedRuleSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['rule_id'], namespace=namespace, user_scope="global")  # 10 minutes - cache rule by ID
    def get_by_id(rule_id: str) -> Optional[ParsedRule]:
        """Get parsed rule by ID."""
        try:
            pr = ParsedRuleSelector.get_by_id(rule_id)
            if not pr:
                logger.error(f"Parsed rule {rule_id} not found")
                return None
            return pr
        except Exception as e:
            logger.error(f"Error fetching parsed rule {rule_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda pr: pr is not None)
    def update_status(rule_id: str, status: str, version: int = None) -> Optional[ParsedRule]:
        """Update parsed rule status."""
        try:
            parsed_rule = ParsedRuleSelector.get_by_id(rule_id)
            if not parsed_rule:
                logger.error(f"Parsed rule {rule_id} not found")
                return None
            return ParsedRuleRepository.update_parsed_rule(
                parsed_rule,
                version=version if version is not None else getattr(parsed_rule, "version", None),
                status=status,
            )
        except Exception as e:
            logger.error(f"Error updating parsed rule {rule_id} status: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda pr: pr is not None)
    def update_parsed_rule(rule_id: str, **fields) -> Optional[ParsedRule]:
        """Update parsed rule fields."""
        try:
            parsed_rule = ParsedRuleSelector.get_by_id(rule_id)
            if not parsed_rule:
                logger.error(f"Parsed rule {rule_id} not found")
                return None
            expected_version = fields.pop("version", None)
            return ParsedRuleRepository.update_parsed_rule(
                parsed_rule,
                version=expected_version if expected_version is not None else getattr(parsed_rule, "version", None),
                **fields
            )
        except Exception as e:
            logger.error(f"Error updating parsed rule {rule_id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_parsed_rule(rule_id: str) -> bool:
        """Delete a parsed rule."""
        try:
            parsed_rule = ParsedRuleSelector.get_by_id(rule_id)
            if not parsed_rule:
                logger.error(f"Parsed rule {rule_id} not found")
                return False
            ParsedRuleRepository.delete_parsed_rule(parsed_rule, version=getattr(parsed_rule, "version", None))
            return True
        except Exception as e:
            logger.error(f"Error deleting parsed rule {rule_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(status: str = None, visa_code: str = None, rule_type: str = None, min_confidence: float = None, date_from=None, date_to=None):
        """Get parsed rules with filters."""
        try:
            return ParsedRuleSelector.get_by_filters(
                status=status,
                visa_code=visa_code,
                rule_type=rule_type,
                min_confidence=min_confidence,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error fetching filtered parsed rules: {e}")
            return ParsedRuleSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get parsed rule statistics."""
        try:
            return ParsedRuleSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting parsed rule statistics: {e}")
            return {}
