import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result
from rules_knowledge.models.visa_document_requirement import VisaDocumentRequirement
from rules_knowledge.repositories.visa_document_requirement_repository import VisaDocumentRequirementRepository
from rules_knowledge.selectors.visa_document_requirement_selector import VisaDocumentRequirementSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector
from compliance.services.audit_log_service import AuditLogService

logger = logging.getLogger('django')


class VisaDocumentRequirementService:
    """Service for VisaDocumentRequirement business logic."""

    @staticmethod
    def create_document_requirement(rule_version_id: str, document_type_id: str,
                                   mandatory: bool = True, conditional_logic: dict = None):
        """Create a new document requirement."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            document_type = DocumentTypeSelector.get_by_id(document_type_id)
            doc_requirement = VisaDocumentRequirementRepository.create_document_requirement(
                rule_version, document_type, mandatory, conditional_logic
            )
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Document requirement created: {document_type.code} for rule version {rule_version_id} (mandatory={mandatory})",
                    func_name='create_document_requirement',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return doc_requirement
        except Exception as e:
            logger.error(f"Error creating document requirement: {e}", exc_info=True)
            return None

    @staticmethod
    @cache_result(timeout=600, keys=[])  # 10 minutes - can change when requirements are updated
    def get_all():
        """Get all document requirements."""
        try:
            return VisaDocumentRequirementSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document requirements: {e}")
            return VisaDocumentRequirement.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['rule_version_id'])  # 1 hour - requirements per version change infrequently
    def get_by_rule_version(rule_version_id: str):
        """Get document requirements by rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            return VisaDocumentRequirementSelector.get_by_rule_version(rule_version)
        except Exception as e:
            logger.error(f"Error fetching document requirements for rule version {rule_version_id}: {e}")
            return VisaDocumentRequirement.objects.none()

    @staticmethod
    @cache_result(timeout=3600, keys=['requirement_id'])  # 1 hour - cache by requirement ID
    def get_by_id(requirement_id: str) -> Optional[VisaDocumentRequirement]:
        """Get document requirement by ID."""
        try:
            return VisaDocumentRequirementSelector.get_by_id(requirement_id)
        except VisaDocumentRequirement.DoesNotExist:
            logger.error(f"Document requirement {requirement_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document requirement {requirement_id}: {e}")
            return None

    @staticmethod
    def update_document_requirement(requirement_id: str, **fields) -> Optional[VisaDocumentRequirement]:
        """Update document requirement."""
        try:
            doc_requirement = VisaDocumentRequirementSelector.get_by_id(requirement_id)
            updated_requirement = VisaDocumentRequirementRepository.update_document_requirement(doc_requirement, **fields)
            
            # Log audit event
            try:
                changes = ', '.join([f"{k}={v}" for k, v in fields.items()])
                AuditLogService.create_audit_log(
                    level='INFO',
                    logger_name='rules_knowledge',
                    message=f"Document requirement {requirement_id} updated: {changes}",
                    func_name='update_document_requirement',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return updated_requirement
        except VisaDocumentRequirement.DoesNotExist:
            logger.error(f"Document requirement {requirement_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating document requirement {requirement_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def delete_document_requirement(requirement_id: str) -> bool:
        """Delete document requirement."""
        try:
            doc_requirement = VisaDocumentRequirementSelector.get_by_id(requirement_id)
            VisaDocumentRequirementRepository.delete_document_requirement(doc_requirement)
            
            # Log audit event
            try:
                AuditLogService.create_audit_log(
                    level='WARNING',
                    logger_name='rules_knowledge',
                    message=f"Document requirement {requirement_id} deleted: {doc_requirement.document_type.code}",
                    func_name='delete_document_requirement',
                    pathname=__file__
                )
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {audit_error}")
            
            return True
        except VisaDocumentRequirement.DoesNotExist:
            logger.error(f"Document requirement {requirement_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document requirement {requirement_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def get_by_filters(rule_version_id=None, document_type_id=None, mandatory=None, visa_type_id=None, jurisdiction=None, date_from=None, date_to=None):
        """Get document requirements with advanced filtering for admin."""
        try:
            return VisaDocumentRequirementSelector.get_by_filters(
                rule_version_id=rule_version_id,
                document_type_id=document_type_id,
                mandatory=mandatory,
                visa_type_id=visa_type_id,
                jurisdiction=jurisdiction,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error filtering document requirements: {e}")
            return VisaDocumentRequirement.objects.none()
