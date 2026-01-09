import logging
from typing import Optional
from data_ingestion.models.document_diff import DocumentDiff
from data_ingestion.selectors.document_diff_selector import DocumentDiffSelector

logger = logging.getLogger('django')


class DocumentDiffService:
    """Service for DocumentDiff business logic."""

    @staticmethod
    def get_all():
        """Get all document diffs."""
        try:
            return DocumentDiffSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document diffs: {e}")
            return DocumentDiff.objects.none()

    @staticmethod
    def get_by_change_type(change_type: str):
        """Get document diffs by change type."""
        try:
            return DocumentDiffSelector.get_by_change_type(change_type)
        except Exception as e:
            logger.error(f"Error fetching document diffs by change type {change_type}: {e}")
            return DocumentDiff.objects.none()

    @staticmethod
    def get_by_id(diff_id: str) -> Optional[DocumentDiff]:
        """Get document diff by ID."""
        try:
            return DocumentDiffSelector.get_by_id(diff_id)
        except DocumentDiff.DoesNotExist:
            logger.error(f"Document diff {diff_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document diff {diff_id}: {e}")
            return None

    @staticmethod
    def get_by_versions(old_version_id: str, new_version_id: str) -> Optional[DocumentDiff]:
        """Get document diff between two versions."""
        try:
            from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
            old_version = DocumentVersionSelector.get_by_id(old_version_id)
            new_version = DocumentVersionSelector.get_by_id(new_version_id)
            if not old_version or not new_version:
                return None
            return DocumentDiffSelector.get_by_versions(old_version, new_version)
        except Exception as e:
            logger.error(f"Error fetching document diff between versions {old_version_id} and {new_version_id}: {e}")
            return None

