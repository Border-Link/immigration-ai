import logging
from typing import Optional
from django.utils import timezone
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.repositories.visa_rule_version_repository import VisaRuleVersionRepository
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.visa_type_selector import VisaTypeSelector

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
            
            return VisaRuleVersionRepository.create_rule_version(
                visa_type, effective_from, effective_to, source_doc_version, is_published, created_by
            )
        except Exception as e:
            logger.error(f"Error creating rule version for visa type {visa_type_id}: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all rule versions."""
        try:
            return VisaRuleVersionSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all rule versions: {e}")
            return VisaRuleVersion.objects.none()

    @staticmethod
    def get_by_visa_type(visa_type_id: str):
        """Get rule versions by visa type."""
        try:
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            return VisaRuleVersionSelector.get_by_visa_type(visa_type)
        except Exception as e:
            logger.error(f"Error fetching rule versions for visa type {visa_type_id}: {e}")
            return VisaRuleVersion.objects.none()

    @staticmethod
    def get_current_by_visa_type(visa_type_id: str) -> Optional[VisaRuleVersion]:
        """Get current rule version for a visa type."""
        try:
            visa_type = VisaTypeSelector.get_by_id(visa_type_id)
            return VisaRuleVersionSelector.get_current_by_visa_type(visa_type)
        except Exception as e:
            logger.error(f"Error fetching current rule version for visa type {visa_type_id}: {e}")
            return None

    @staticmethod
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
    def publish_rule_version(version_id: str, published_by=None) -> Optional[VisaRuleVersion]:
        """Publish a rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(version_id)
            return VisaRuleVersionRepository.publish_rule_version(rule_version, published_by)
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error publishing rule version {version_id}: {e}")
            return None

    @staticmethod
    def update_rule_version(version_id: str, updated_by=None, **fields) -> Optional[VisaRuleVersion]:
        """Update rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(version_id)
            return VisaRuleVersionRepository.update_rule_version(rule_version, updated_by, **fields)
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating rule version {version_id}: {e}")
            return None

    @staticmethod
    def delete_rule_version(version_id: str) -> bool:
        """Delete rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(version_id)
            VisaRuleVersionRepository.delete_rule_version(rule_version)
            return True
        except VisaRuleVersion.DoesNotExist:
            logger.error(f"Rule version {version_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting rule version {version_id}: {e}")
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
