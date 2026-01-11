import logging
from typing import Optional
from django.utils import timezone
from helpers.cache_utils import cache_result
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.repositories.visa_rule_version_repository import VisaRuleVersionRepository
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')


class VisaRuleVersionService:
    """Service for VisaRuleVersion business logic."""

    @staticmethod
    def create_rule_version(visa_type_id: str, effective_from, effective_to=None,
                           source_document_version_id=None, is_published: bool = False, created_by=None):
        """Create a new rule version."""
        try:
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            source_doc_version = None
            if source_document_version_id:
                from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
                source_doc_version = DocumentVersionSelector.get_by_id(source_document_version_id)
            
            rule_version = VisaRuleVersionRepository.create_rule_version(
                visa_type, effective_from, effective_to, source_doc_version, is_published, created_by
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Rule version created for visa type {visa_type_id}: effective_from={effective_from}, is_published={is_published}",
                    func_name='create_rule_version',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return rule_version
        except Exception as e:
            logger.error(f"Error creating rule version for visa type {visa_type_id}: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=600, keys=[])  # 10 minutes - can change when rules are published
    def get_all():
        """Get all rule versions."""
        try:
            return VisaRuleVersionSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all rule versions: {e}")
            return VisaRuleVersion.objects.none()

    @staticmethod
    @cache_result(timeout=600, keys=['visa_type_id'])  # 10 minutes - cache by visa type
    def get_by_visa_type(visa_type_id: str):
        """Get rule versions by visa type."""
        try:
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            return VisaRuleVersionSelector.get_by_visa_type(visa_type)
        except Exception as e:
            logger.error(f"Error fetching rule versions for visa type {visa_type_id}: {e}")
            return VisaRuleVersion.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['visa_type_id'])  # 1 hour - current version changes infrequently
    def get_current_by_visa_type(visa_type_id: str) -> Optional[VisaRuleVersion]:
        """Get current rule version for a visa type."""
        try:
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            return VisaRuleVersionSelector.get_current_by_visa_type(visa_type)
        except Exception as e:
            logger.error(f"Error fetching current rule version for visa type {visa_type_id}: {e}")
            return None

    @staticmethod
    @cache_result(timeout=3600, keys=['version_id'])  # 1 hour - cache by version ID
    def get_by_id(version_id: str) -> Optional[VisaRuleVersion]:
        """Get rule version by ID."""
        try:
            return VisaRuleVersionSelector.get_by_id(version_id)
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching rule version {version_id}: {e}")
            return None

    @staticmethod
    def publish_rule_version(version_id: str, published_by=None, expected_version=None) -> Optional[VisaRuleVersion]:
        """
        Publish a rule version with optimistic locking support.
        
        Args:
            version_id: UUID of rule version to publish
            published_by: User performing the publish
            expected_version: Expected version number for optimistic locking (None to skip check)
            
        Returns:
            Published VisaRuleVersion instance or None if not found
            
        Raises:
            ValidationError: If version conflict detected (caller should handle)
        """
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(version_id)
            published_version = VisaRuleVersionRepository.publish_rule_version(
                rule_version, published_by, expected_version=expected_version
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Rule version {version_id} published for visa type {rule_version.visa_type.code}",
                    func_name='publish_rule_version',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return published_version
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return None
        except ValidationError:
            # Re-raise ValidationError for version conflicts - let views handle it
            raise
        except Exception as e:
            logger.error(f"Error publishing rule version {version_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def update_rule_version(version_id: str, updated_by=None, expected_version=None, **fields) -> Optional[VisaRuleVersion]:
        """
        Update rule version with optimistic locking support.
        
        Args:
            version_id: UUID of rule version to update
            updated_by: User performing the update
            expected_version: Expected version number for optimistic locking (None to skip check)
            **fields: Fields to update
            
        Returns:
            Updated VisaRuleVersion instance or None if not found
            
        Raises:
            ValidationError: If version conflict detected (caller should handle)
        """
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(version_id)
            updated_version = VisaRuleVersionRepository.update_rule_version(
                rule_version, updated_by, expected_version=expected_version, **fields
            )
            
            # Log audit event
            try:
                changes = ', '.join([f"{k}={v}" for k, v in fields.items()])
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Rule version {version_id} updated: {changes}",
                    func_name='update_rule_version',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_version
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return None
        except ValidationError:
            # Re-raise ValidationError for version conflicts - let views handle it
            raise
        except Exception as e:
            logger.error(f"Error updating rule version {version_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def delete_rule_version(version_id: str) -> bool:
        """Delete rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(version_id)
            VisaRuleVersionRepository.delete_rule_version(rule_version)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='rules_knowledge',
                    message=f"Rule version {version_id} deleted (soft delete) for visa type {rule_version.visa_type.code}",
                    func_name='delete_rule_version',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting rule version {version_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def get_by_filters(visa_type_id=None, is_published=None, jurisdiction=None, date_from=None, date_to=None, effective_from=None, effective_to=None):
        """Get rule versions with advanced filtering for admin."""
        try:
            return VisaRuleVersionSelector.get_by_filters(
                visa_type_id=visa_type_id,
                is_published=is_published,
                jurisdiction=jurisdiction,
                date_from=date_from,
                date_to=date_to,
                effective_from=effective_from,
                effective_to=effective_to
            )
        except Exception as e:
            logger.error(f"Error filtering rule versions: {e}")
            return VisaRuleVersion.objects.none()

    @staticmethod
    def publish_rule_version_by_flag(rule_version, is_published: bool) -> Optional[VisaRuleVersion]:
        """Publish or unpublish a rule version."""
        try:
            return VisaRuleVersionRepository.update_rule_version(rule_version, is_published=is_published)
        except Exception as e:
            logger.error(f"Error publishing/unpublishing rule version: {e}")
            return None
