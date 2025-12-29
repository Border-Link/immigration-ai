from django.db import transaction
from document_handling.models.document_check import DocumentCheck
from document_handling.models.case_document import CaseDocument


class DocumentCheckRepository:
    """Repository for DocumentCheck write operations."""

    @staticmethod
    def create_document_check(case_document: CaseDocument, check_type: str, result: str,
                             details: dict = None, performed_by: str = None):
        """Create a new document check."""
        with transaction.atomic():
            document_check = DocumentCheck.objects.create(
                case_document=case_document,
                check_type=check_type,
                result=result,
                details=details,
                performed_by=performed_by
            )
            document_check.full_clean()
            document_check.save()
            return document_check

    @staticmethod
    def update_document_check(document_check, **fields):
        """Update document check fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(document_check, key):
                    setattr(document_check, key, value)
            document_check.full_clean()
            document_check.save()
            return document_check

    @staticmethod
    def delete_document_check(document_check):
        """Delete a document check."""
        with transaction.atomic():
            document_check.delete()

