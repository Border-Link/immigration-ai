from django.db import transaction
from document_handling.models.case_document import CaseDocument
from immigration_cases.models.case import Case
from rules_knowledge.models.document_type import DocumentType


class CaseDocumentRepository:
    """Repository for CaseDocument write operations."""

    @staticmethod
    def create_case_document(case: Case, document_type: DocumentType, file_path: str,
                            file_name: str, file_size: int = None, mime_type: str = None,
                            status: str = 'uploaded'):
        """Create a new case document."""
        with transaction.atomic():
            case_document = CaseDocument.objects.create(
                case=case,
                document_type=document_type,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                status=status
            )
            case_document.full_clean()
            case_document.save()
            return case_document

    @staticmethod
    def update_case_document(case_document, **fields):
        """Update case document fields."""
        with transaction.atomic():
            for key, value in fields.items():
                if hasattr(case_document, key):
                    setattr(case_document, key, value)
            case_document.full_clean()
            case_document.save()
            return case_document

    @staticmethod
    def update_status(case_document, status: str):
        """Update document status."""
        with transaction.atomic():
            case_document.status = status
            case_document.full_clean()
            case_document.save()
            return case_document

    @staticmethod
    def delete_case_document(case_document):
        """Delete a case document."""
        with transaction.atomic():
            case_document.delete()

