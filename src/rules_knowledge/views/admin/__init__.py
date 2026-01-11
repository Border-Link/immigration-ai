"""
Admin Views for Rules Knowledge Management

Admin-only views for managing rules knowledge models.
"""
from .document_type_admin import (
    DocumentTypeAdminListAPI,
    DocumentTypeAdminDetailAPI,
    DocumentTypeAdminActivateAPI,
    DocumentTypeAdminDeleteAPI,
    BulkDocumentTypeOperationAPI,
)
from .visa_type_admin import (
    VisaTypeAdminListAPI,
    VisaTypeAdminDetailAPI,
    VisaTypeAdminActivateAPI,
    VisaTypeAdminDeleteAPI,
    BulkVisaTypeOperationAPI,
)
from .visa_rule_version_admin import (
    VisaRuleVersionAdminListAPI,
    VisaRuleVersionAdminDetailAPI,
    VisaRuleVersionAdminUpdateAPI,
    VisaRuleVersionAdminPublishAPI,
    VisaRuleVersionAdminDeleteAPI,
    BulkVisaRuleVersionOperationAPI,
)
from .visa_requirement_admin import (
    VisaRequirementAdminListAPI,
    VisaRequirementAdminDetailAPI,
    VisaRequirementAdminUpdateAPI,
    VisaRequirementAdminDeleteAPI,
    BulkVisaRequirementOperationAPI,
)
from .visa_document_requirement_admin import (
    VisaDocumentRequirementAdminListAPI,
    VisaDocumentRequirementAdminDetailAPI,
    VisaDocumentRequirementAdminUpdateAPI,
    VisaDocumentRequirementAdminDeleteAPI,
    BulkVisaDocumentRequirementOperationAPI,
)
from .rules_knowledge_analytics import RulesKnowledgeStatisticsAPI

__all__ = [
    # DocumentType Admin
    'DocumentTypeAdminListAPI',
    'DocumentTypeAdminDetailAPI',
    'DocumentTypeAdminActivateAPI',
    'DocumentTypeAdminDeleteAPI',
    'BulkDocumentTypeOperationAPI',
    # VisaType Admin
    'VisaTypeAdminListAPI',
    'VisaTypeAdminDetailAPI',
    'VisaTypeAdminActivateAPI',
    'VisaTypeAdminDeleteAPI',
    'BulkVisaTypeOperationAPI',
    # VisaRuleVersion Admin
    'VisaRuleVersionAdminListAPI',
    'VisaRuleVersionAdminDetailAPI',
    'VisaRuleVersionAdminUpdateAPI',
    'VisaRuleVersionAdminPublishAPI',
    'VisaRuleVersionAdminDeleteAPI',
    'BulkVisaRuleVersionOperationAPI',
    # VisaRequirement Admin
    'VisaRequirementAdminListAPI',
    'VisaRequirementAdminDetailAPI',
    'VisaRequirementAdminUpdateAPI',
    'VisaRequirementAdminDeleteAPI',
    'BulkVisaRequirementOperationAPI',
    # VisaDocumentRequirement Admin
    'VisaDocumentRequirementAdminListAPI',
    'VisaDocumentRequirementAdminDetailAPI',
    'VisaDocumentRequirementAdminUpdateAPI',
    'VisaDocumentRequirementAdminDeleteAPI',
    'BulkVisaDocumentRequirementOperationAPI',
    # Analytics
    'RulesKnowledgeStatisticsAPI',
]
