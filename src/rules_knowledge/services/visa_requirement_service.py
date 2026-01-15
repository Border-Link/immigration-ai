import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result, invalidate_cache
from rules_knowledge.models.visa_requirement import VisaRequirement
from rules_knowledge.repositories.visa_requirement_repository import VisaRequirementRepository
from rules_knowledge.selectors.visa_requirement_selector import VisaRequirementSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    return "visa_requirements"


class VisaRequirementService:
    """Service for VisaRequirement business logic."""

    @staticmethod
    @invalidate_cache(namespace, predicate=lambda req: req is not None)
    def create_requirement(rule_version_id: str, requirement_code: str, rule_type: str,
                          description: str, condition_expression: dict, is_mandatory: bool = True):
        """Create a new visa requirement."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            requirement = VisaRequirementRepository.create_requirement(
                rule_version, requirement_code, rule_type, description, condition_expression, is_mandatory
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Visa requirement created: {requirement_code} for rule version {rule_version_id}",
                    func_name='create_requirement',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return requirement
        except Exception as e:
            logger.error(f"Error creating requirement {requirement_code}: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=600, keys=[], namespace=namespace, user_scope="global")  # 10 minutes - can change when requirements are updated
    def get_all():
        """Get all requirements."""
        try:
            return VisaRequirementSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all requirements: {e}")
            return VisaRequirement.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['rule_version_id'], namespace=namespace, user_scope="global")  # 1 hour - requirements per version change infrequently
    def get_by_rule_version(rule_version_id: str):
        """Get requirements by rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            return VisaRequirementSelector.get_by_rule_version(rule_version)
        except Exception as e:
            logger.error(f"Error fetching requirements for rule version {rule_version_id}: {e}")
            return VisaRequirement.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['requirement_id'], namespace=namespace, user_scope="global")  # 1 hour - cache by requirement ID
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
    @invalidate_cache(namespace, predicate=lambda req: req is not None)
    def update_requirement(requirement_id: str, **fields) -> Optional[VisaRequirement]:
        """Update requirement."""
        try:
            requirement = VisaRequirementSelector.get_by_id(requirement_id)
            updated_requirement = VisaRequirementRepository.update_requirement(requirement, **fields)
            
            # Log audit event
            try:
                changes = ', '.join([f"{k}={v}" for k, v in fields.items()])
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Visa requirement {requirement_id} updated: {changes}",
                    func_name='update_requirement',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_requirement
        except VisaRequirement.DoesNotExist:
            logger.error(f"Requirement {requirement_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating requirement {requirement_id}: {e}", exc_info=True)
            return None

    @staticmethod
    @invalidate_cache(namespace, predicate=bool)
    def delete_requirement(requirement_id: str) -> bool:
        """Delete requirement."""
        try:
            requirement = VisaRequirementSelector.get_by_id(requirement_id)
            VisaRequirementRepository.delete_requirement(requirement)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='rules_knowledge',
                    message=f"Visa requirement {requirement_id} deleted: {requirement.requirement_code}",
                    func_name='delete_requirement',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except VisaRequirement.DoesNotExist:
            logger.error(f"Requirement {requirement_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting requirement {requirement_id}: {e}", exc_info=True)
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

    @staticmethod
    def create_visa_requirement(rule_version_id: str, requirement_code: str, description: str,
                               condition_expression: dict, is_active: bool = True):
        """
        Create a new visa requirement (wrapper method for views).
        Maps is_active to is_mandatory and defaults rule_type to 'eligibility'.
        """
        return VisaRequirementService.create_requirement(
            rule_version_id=rule_version_id,
            requirement_code=requirement_code,
            rule_type='eligibility',  # Default to eligibility if not specified
            description=description,
            condition_expression=condition_expression,
            is_mandatory=is_active  # Map is_active to is_mandatory
        )

    @staticmethod
    def update_visa_requirement(requirement_id: str, **fields) -> Optional[VisaRequirement]:
        """Update visa requirement (alias for update_requirement)."""
        return VisaRequirementService.update_requirement(requirement_id, **fields)

    @staticmethod
    def delete_visa_requirement(requirement_id: str) -> bool:
        """Delete visa requirement (alias for delete_requirement)."""
        return VisaRequirementService.delete_requirement(requirement_id)
