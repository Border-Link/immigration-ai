# DocumentType views
from .document_type.create import DocumentTypeCreateAPI
from .document_type.read import DocumentTypeListAPI, DocumentTypeDetailAPI
from .document_type.update_delete import DocumentTypeUpdateAPI, DocumentTypeDeleteAPI

# VisaType views
from .visa_type.create import VisaTypeCreateAPI
from .visa_type.read import VisaTypeListAPI, VisaTypeDetailAPI
from .visa_type.update_delete import VisaTypeUpdateAPI, VisaTypeDeleteAPI

# VisaRuleVersion views
from .visa_rule_version.create import VisaRuleVersionCreateAPI
from .visa_rule_version.read import VisaRuleVersionListAPI, VisaRuleVersionDetailAPI
from .visa_rule_version.update_delete import VisaRuleVersionUpdateAPI, VisaRuleVersionDeleteAPI

# VisaRequirement views
from .visa_requirement.create import VisaRequirementCreateAPI
from .visa_requirement.read import VisaRequirementListAPI, VisaRequirementDetailAPI
from .visa_requirement.update_delete import VisaRequirementUpdateAPI, VisaRequirementDeleteAPI

# VisaDocumentRequirement views
from .visa_document_requirement.create import VisaDocumentRequirementCreateAPI
from .visa_document_requirement.read import VisaDocumentRequirementListAPI, VisaDocumentRequirementDetailAPI
from .visa_document_requirement.update_delete import VisaDocumentRequirementUpdateAPI, VisaDocumentRequirementDeleteAPI

# Admin views
from .admin import (
    DocumentTypeAdminListAPI,
    DocumentTypeAdminDetailAPI,
    DocumentTypeAdminActivateAPI,
    DocumentTypeAdminDeleteAPI,
    BulkDocumentTypeOperationAPI,
    VisaTypeAdminListAPI,
    VisaTypeAdminDetailAPI,
    VisaTypeAdminActivateAPI,
    VisaTypeAdminDeleteAPI,
    BulkVisaTypeOperationAPI,
    VisaRuleVersionAdminListAPI,
    VisaRuleVersionAdminDetailAPI,
    VisaRuleVersionAdminUpdateAPI,
    VisaRuleVersionAdminPublishAPI,
    VisaRuleVersionAdminDeleteAPI,
    BulkVisaRuleVersionOperationAPI,
    VisaRequirementAdminListAPI,
    VisaRequirementAdminDetailAPI,
    VisaRequirementAdminUpdateAPI,
    VisaRequirementAdminDeleteAPI,
    BulkVisaRequirementOperationAPI,
    VisaDocumentRequirementAdminListAPI,
    VisaDocumentRequirementAdminDetailAPI,
    VisaDocumentRequirementAdminUpdateAPI,
    VisaDocumentRequirementAdminDeleteAPI,
    BulkVisaDocumentRequirementOperationAPI,
    RulesKnowledgeStatisticsAPI,
)

__all__ = [
    # DocumentType
    'DocumentTypeCreateAPI',
    'DocumentTypeListAPI',
    'DocumentTypeDetailAPI',
    'DocumentTypeUpdateAPI',
    'DocumentTypeDeleteAPI',
    # VisaType
    'VisaTypeCreateAPI',
    'VisaTypeListAPI',
    'VisaTypeDetailAPI',
    'VisaTypeUpdateAPI',
    'VisaTypeDeleteAPI',
    # VisaRuleVersion
    'VisaRuleVersionCreateAPI',
    'VisaRuleVersionListAPI',
    'VisaRuleVersionDetailAPI',
    'VisaRuleVersionUpdateAPI',
    'VisaRuleVersionDeleteAPI',
    # VisaRequirement
    'VisaRequirementCreateAPI',
    'VisaRequirementListAPI',
    'VisaRequirementDetailAPI',
    'VisaRequirementUpdateAPI',
    'VisaRequirementDeleteAPI',
    # VisaDocumentRequirement
    'VisaDocumentRequirementCreateAPI',
    'VisaDocumentRequirementListAPI',
    'VisaDocumentRequirementDetailAPI',
    'VisaDocumentRequirementUpdateAPI',
    'VisaDocumentRequirementDeleteAPI',
    # Admin views
    'DocumentTypeAdminListAPI',
    'DocumentTypeAdminDetailAPI',
    'DocumentTypeAdminActivateAPI',
    'DocumentTypeAdminDeleteAPI',
    'BulkDocumentTypeOperationAPI',
    'VisaTypeAdminListAPI',
    'VisaTypeAdminDetailAPI',
    'VisaTypeAdminActivateAPI',
    'VisaTypeAdminDeleteAPI',
    'BulkVisaTypeOperationAPI',
    'VisaRuleVersionAdminListAPI',
    'VisaRuleVersionAdminDetailAPI',
    'VisaRuleVersionAdminUpdateAPI',
    'VisaRuleVersionAdminPublishAPI',
    'VisaRuleVersionAdminDeleteAPI',
    'BulkVisaRuleVersionOperationAPI',
    'VisaRequirementAdminListAPI',
    'VisaRequirementAdminDetailAPI',
    'VisaRequirementAdminUpdateAPI',
    'VisaRequirementAdminDeleteAPI',
    'BulkVisaRequirementOperationAPI',
    'VisaDocumentRequirementAdminListAPI',
    'VisaDocumentRequirementAdminDetailAPI',
    'VisaDocumentRequirementAdminUpdateAPI',
    'VisaDocumentRequirementAdminDeleteAPI',
    'BulkVisaDocumentRequirementOperationAPI',
    'RulesKnowledgeStatisticsAPI',
]

