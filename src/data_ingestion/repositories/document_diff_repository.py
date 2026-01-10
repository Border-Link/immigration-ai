from django.db import transaction
from data_ingestion.models.document_diff import DocumentDiff
from data_ingestion.models.document_version import DocumentVersion


class DocumentDiffRepository:
    """Repository for DocumentDiff write operations."""

    @staticmethod
    def create_document_diff(old_version: DocumentVersion, new_version: DocumentVersion,
                            diff_text: str, change_type: str = 'minor_text'):
        """Create a new document diff."""
        with transaction.atomic():
            # Check if diff already exists
            existing = DocumentDiff.objects.filter(
                old_version=old_version,
                new_version=new_version
            ).first()
            if existing:
                return existing
            
            diff = DocumentDiff.objects.create(
                old_version=old_version,
                new_version=new_version,
                diff_text=diff_text,
                change_type=change_type
            )
            diff.full_clean()
            diff.save()
            return diff

    @staticmethod
    def delete_document_diff(document_diff):
        """Delete a document diff."""
        with transaction.atomic():
            document_diff.delete()
            return True
