import logging
from typing import Optional
from rules_knowledge.models.visa_document_requirement import VisaDocumentRequirement
from rules_knowledge.repositories.visa_document_requirement_repository import VisaDocumentRequirementRepository
from rules_knowledge.selectors.visa_document_requirement_selector import VisaDocumentRequirementSelector
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector
from rules_knowledge.selectors.document_type_selector import DocumentTypeSelector

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
            return VisaDocumentRequirementRepository.create_document_requirement(
                rule_version, document_type, mandatory, conditional_logic
            )
        except Exception as e:
            logger.error(f"Error creating document requirement: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all document requirements."""
        try:
            return VisaDocumentRequirementSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document requirements: {e}")
            return VisaDocumentRequirement.objects.none()

    @staticmethod
    def get_by_rule_version(rule_version_id: str):
        """Get document requirements by rule version."""
        try:
            rule_version = VisaRuleVersionSelector.get_by_id(rule_version_id)
            return VisaDocumentRequirementSelector.get_by_rule_version(rule_version)
        except Exception as e:
            logger.error(f"Error fetching document requirements for rule version {rule_version_id}: {e}")
            return VisaDocumentRequirement.objects.none()

    @staticmethod
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
            return VisaDocumentRequirementRepository.update_document_requirement(doc_requirement, **fields)
        except VisaDocumentRequirement.DoesNotExist:
            logger.error(f"Document requirement {requirement_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating document requirement {requirement_id}: {e}")
            return None

    @staticmethod
    def delete_document_requirement(requirement_id: str) -> bool:
        """Delete document requirement."""
        try:
            doc_requirement = VisaDocumentRequirementSelector.get_by_id(requirement_id)
            VisaDocumentRequirementRepository.delete_document_requirement(doc_requirement)
            return True
        except VisaDocumentRequirement.DoesNotExist:
            logger.error(f"Document requirement {requirement_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document requirement {requirement_id}: {e}")
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
