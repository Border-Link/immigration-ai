import logging
from typing import Optional
from helpers.cache_utils import cache_result
from rules_knowledge.models.visa_requirement import VisaRequirement
from rules_knowledge.repositories.visa_requirement_repository import VisaRequirementRepository
from rules_knowledge.selectors.visa_requirement_selector import VisaRequirementSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector

logger = logging.getLogger('django')


class VisaRequirementService:
    """Service for VisaRequirement business logic."""

    @staticmethod
    def create_requirement(rule_version_id: str, requirement_code: str, rule_type: str,
                          description: str, condition_expression: dict, is_mandatory: bool = True):
        """Create a new visa requirement."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            return VisaRequirementRepository.create_requirement(
                rule_version, requirement_code, rule_type, description, condition_expression, is_mandatory
            )
        except Exception as e:
            logger.error(f"Error creating requirement {requirement_code}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=600, keys=[])  # 10 minutes - can change when requirements are updated
    def get_all():
        """Get all requirements."""
        try:
            return VisaRequirementSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all requirements: {e}")
            return VisaRequirement.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['rule_version_id'])  # 1 hour - requirements per version change infrequently
    def get_by_rule_version(rule_version_id: str):
        """Get requirements by rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            return VisaRequirementSelector.get_by_rule_version(rule_version)
        except Exception as e:
            logger.error(f"Error fetching requirements for rule version {rule_version_id}: {e}")
            return VisaRequirement.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['requirement_id'])  # 1 hour - cache by requirement ID
    def get_by_id(requirement_id: str) -> Optional[VisaRequirement]:
        """Get requirement by ID."""
        try:
            return VisaRequirementSelector.get_by_id(requirement_id)
        except VisaRequirement.DoesNotExist:
            logger.error(f"Requirement {requirement_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching requirement {requirement_id}: {e}")
            return None

    @staticmethod
    def update_requirement(requirement_id: str, **fields) -> Optional[VisaRequirement]:
        """Update requirement."""
        try:
            requirement = VisaRequirementSelector.get_by_id(requirement_id)
            return VisaRequirementRepository.update_requirement(requirement, **fields)
        except VisaRequirement.DoesNotExist:
            logger.error(f"Requirement {requirement_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating requirement {requirement_id}: {e}")
            return None

    @staticmethod
    def delete_requirement(requirement_id: str) -> bool:
        """Delete requirement."""
        try:
            requirement = VisaRequirementSelector.get_by_id(requirement_id)
            VisaRequirementRepository.delete_requirement(requirement)
            return True
        except VisaRequirement.DoesNotExist:
            logger.error(f"Requirement {requirement_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting requirement {requirement_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(rule_version_id=None, rule_type=None, is_mandatory=None, requirement_code=None, visa_type_id=None, jurisdiction=None, date_from=None, date_to=None):
        """Get requirements with advanced filtering for admin."""
        try:
            return VisaRequirementSelector.get_by_filters(
                rule_version_id=rule_version_id,
                rule_type=rule_type,
                is_mandatory=is_mandatory,
                requirement_code=requirement_code,
                visa_type_id=visa_type_id,
                jurisdiction=jurisdiction,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering requirements: {e}")
            return VisaRequirement.objects.none()
