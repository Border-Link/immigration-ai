import logging
from typing import Optional
from main_system.utils.cache_utils import cache_result
from document_handling.models.document_check import DocumentCheck
from document_handling.models.case_document import CaseDocument
from document_handling.repositories.document_check_repository import DocumentCheckRepository
from document_handling.selectors.document_check_selector import DocumentCheckSelector
from document_handling.selectors.case_document_selector import CaseDocumentSelector

logger = logging.getLogger('django')


class DocumentCheckService:
    """Service for DocumentCheck business logic."""

    @staticmethod
    def create_document_check(case_document_id: str, check_type: str, result: str,
                             details: dict = None, performed_by: str = None):
        """Create a new document check."""
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            return DocumentCheckRepository.create_document_check(
                case_document=case_document,
                check_type=check_type,
                result=result,
                details=details,
                performed_by=performed_by
            )
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {case_document_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error creating document check: {e}")
            return None

    @staticmethod
    @cache_result(timeout=300, keys=[])  # 5 minutes - document checks change frequently
    def get_all():
        """Get all document checks."""
        try:
            return DocumentCheckSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all document checks: {e}")
            return DocumentCheckSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['case_document_id'])  # 5 minutes - cache checks by case document
    def get_by_case_document(case_document_id: str):
        """Get checks by case document."""
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            return DocumentCheckSelector.get_by_case_document(case_document)
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {case_document_id} not found")
            return DocumentCheckSelector.get_none()
        except Exception as e:
            logger.error(f"Error fetching checks for case document {case_document_id}: {e}")
            return DocumentCheckSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['check_type'])  # 5 minutes - cache checks by type
    def get_by_check_type(check_type: str):
        """Get checks by check type."""
        try:
            return DocumentCheckSelector.get_by_check_type(check_type)
        except Exception as e:
            logger.error(f"Error fetching checks by type {check_type}: {e}")
            return DocumentCheckSelector.get_none()

    @staticmethod
    @cache_result(timeout=300, keys=['result'])  # 5 minutes - cache checks by result
    def get_by_result(result: str):
        """Get checks by result."""
        try:
            return DocumentCheckSelector.get_by_result(result)
        except Exception as e:
            logger.error(f"Error fetching checks by result {result}: {e}")
            return DocumentCheckSelector.get_none()

    @staticmethod
    @cache_result(timeout=600, keys=['check_id'])  # 10 minutes - cache check by ID
    def get_by_id(check_id: str) -> Optional[DocumentCheck]:
        """Get document check by ID."""
        try:
            return DocumentCheckSelector.get_by_id(check_id)
        except DocumentCheck.DoesNotExist:
            logger.error(f"Document check {check_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching document check {check_id}: {e}")
            return None

    @staticmethod
    def update_document_check(check_id: str, **fields) -> Optional[DocumentCheck]:
        """Update document check."""
        try:
            document_check = DocumentCheckSelector.get_by_id(check_id)
            return DocumentCheckRepository.update_document_check(document_check, **fields)
        except DocumentCheck.DoesNotExist:
            logger.error(f"Document check {check_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating document check {check_id}: {e}")
            return None

    @staticmethod
    def delete_document_check(check_id: str) -> bool:
        """Delete document check."""
        try:
            document_check = DocumentCheckSelector.get_by_id(check_id)
            DocumentCheckRepository.delete_document_check(document_check)
            return True
        except DocumentCheck.DoesNotExist:
            logger.error(f"Document check {check_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting document check {check_id}: {e}")
            return False

    @staticmethod
    def get_latest_by_case_document(case_document_id: str, check_type: str = None) -> Optional[DocumentCheck]:
        """Get latest check for a case document."""
        try:
            case_document = CaseDocumentSelector.get_by_id(case_document_id)
            return DocumentCheckSelector.get_latest_by_case_document(case_document, check_type)
        except CaseDocument.DoesNotExist:
            logger.error(f"Case document {case_document_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching latest check for case document {case_document_id}: {e}")
            return None

    @staticmethod
    def get_by_filters(case_document_id: str = None, check_type: str = None, result: str = None,
                       performed_by: str = None, date_from=None, date_to=None):
        """Get document checks with filters."""
        try:
            return DocumentCheckSelector.get_by_filters(
                case_document_id=case_document_id,
                check_type=check_type,
                result=result,
                performed_by=performed_by,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error fetching filtered document checks: {e}")
            return DocumentCheckSelector.get_none()

    @staticmethod
    def get_statistics():
        """Get document check statistics."""
        try:
            return DocumentCheckSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting document check statistics: {e}")
            return {}
