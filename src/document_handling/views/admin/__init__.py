"""
Admin views for document_handling module.
"""
from .case_document_admin import (
    CaseDocumentAdminListAPI,
    CaseDocumentAdminDetailAPI,
    CaseDocumentAdminUpdateAPI,
    CaseDocumentAdminDeleteAPI,
    BulkCaseDocumentOperationAPI,
)
from .document_check_admin import (
    DocumentCheckAdminListAPI,
    DocumentCheckAdminDetailAPI,
    DocumentCheckAdminUpdateAPI,
    DocumentCheckAdminDeleteAPI,
    BulkDocumentCheckOperationAPI,
)
from .document_handling_analytics import DocumentHandlingStatisticsAPI

__all__ = [
    'CaseDocumentAdminListAPI',
    'CaseDocumentAdminDetailAPI',
    'CaseDocumentAdminUpdateAPI',
    'CaseDocumentAdminDeleteAPI',
    'BulkCaseDocumentOperationAPI',
    'DocumentCheckAdminListAPI',
    'DocumentCheckAdminDetailAPI',
    'DocumentCheckAdminUpdateAPI',
    'DocumentCheckAdminDeleteAPI',
    'BulkDocumentCheckOperationAPI',
    'DocumentHandlingStatisticsAPI',
]
