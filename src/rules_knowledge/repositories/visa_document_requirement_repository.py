from django.db import transaction
from rules_knowledge.models.visa_document_requirement import VisaDocumentRequirement
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.document_type import DocumentType


class VisaDocumentRequirementRepository:
    """Repository for VisaDocumentRequirement write operations."""

    @staticmethod
    def create_document_requirement(rule_version: VisaRuleVersion, document_type: DocumentType,
                                   mandatory: bool = True, conditional_logic: dict = None):
        """Create a new document requirement."""
        with transaction.atomic():
            doc_requirement = VisaDocumentRequirement.objects.create(
                rule_version=rule_version,
                document_type=document_type,
                mandatory=mandatory,
                conditional_logic=conditional_logic
            )
            doc_requirement.full_clean()
            doc_requirement.save()
            return doc_requirement

    @staticmethod
    def update_document_requirement(doc_requirement, **fields):
        """Update document requirement fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(doc_requirement, key):
                    setattr(doc_requirement, key, value)
            doc_requirement.full_clean()
            doc_requirement.save()
            return doc_requirement

    @staticmethod
    def delete_document_requirement(doc_requirement):
        """Delete a document requirement."""
        with transaction.atomic():
            # Store values before deletion for cache invalidation
            doc_requirement_id = doc_requirement.id
            rule_version_id = doc_requirement.rule_version.id
            
            doc_requirement.delete()
