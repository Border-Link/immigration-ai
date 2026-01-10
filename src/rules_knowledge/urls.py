from django.urls import path
from rules_knowledge.views import (
    # DocumentType
    DocumentTypeCreateAPI,
    DocumentTypeListAPI,
    DocumentTypeDetailAPI,
    DocumentTypeUpdateAPI,
    DocumentTypeDeleteAPI,
    # VisaType
    VisaTypeCreateAPI,
    VisaTypeListAPI,
    VisaTypeDetailAPI,
    VisaTypeUpdateAPI,
    VisaTypeDeleteAPI,
    # VisaRuleVersion
    VisaRuleVersionCreateAPI,
    VisaRuleVersionListAPI,
    VisaRuleVersionDetailAPI,
    VisaRuleVersionUpdateAPI,
    VisaRuleVersionDeleteAPI,
    # VisaRequirement
    VisaRequirementCreateAPI,
    VisaRequirementListAPI,
    VisaRequirementDetailAPI,
    VisaRequirementUpdateAPI,
    VisaRequirementDeleteAPI,
    # VisaDocumentRequirement
    VisaDocumentRequirementCreateAPI,
    VisaDocumentRequirementListAPI,
    VisaDocumentRequirementDetailAPI,
    VisaDocumentRequirementUpdateAPI,
    VisaDocumentRequirementDeleteAPI,
)
from rules_knowledge.views.admin import (
    # DocumentType Admin
    DocumentTypeAdminListAPI,
    DocumentTypeAdminDetailAPI,
    DocumentTypeAdminActivateAPI,
    DocumentTypeAdminDeleteAPI,
    BulkDocumentTypeOperationAPI,
    # VisaType Admin
    VisaTypeAdminListAPI,
    VisaTypeAdminDetailAPI,
    VisaTypeAdminActivateAPI,
    VisaTypeAdminDeleteAPI,
    BulkVisaTypeOperationAPI,
    # VisaRuleVersion Admin
    VisaRuleVersionAdminListAPI,
    VisaRuleVersionAdminDetailAPI,
    VisaRuleVersionAdminUpdateAPI,
    VisaRuleVersionAdminPublishAPI,
    VisaRuleVersionAdminDeleteAPI,
    BulkVisaRuleVersionOperationAPI,
    # VisaRequirement Admin
    VisaRequirementAdminListAPI,
    VisaRequirementAdminDetailAPI,
    VisaRequirementAdminUpdateAPI,
    VisaRequirementAdminDeleteAPI,
    BulkVisaRequirementOperationAPI,
    # VisaDocumentRequirement Admin
    VisaDocumentRequirementAdminListAPI,
    VisaDocumentRequirementAdminDetailAPI,
    VisaDocumentRequirementAdminUpdateAPI,
    VisaDocumentRequirementAdminDeleteAPI,
    BulkVisaDocumentRequirementOperationAPI,
    # Analytics
    RulesKnowledgeStatisticsAPI,
)

app_name = 'rules_knowledge'

urlpatterns = [
    # DocumentType endpoints
    path('document-types/', DocumentTypeListAPI.as_view(), name='document-type-list'),
    path('document-types/create/', DocumentTypeCreateAPI.as_view(), name='document-type-create'),
    path('document-types/<uuid:id>/', DocumentTypeDetailAPI.as_view(), name='document-type-detail'),
    path('document-types/<uuid:id>/update/', DocumentTypeUpdateAPI.as_view(), name='document-type-update'),
    path('document-types/<uuid:id>/delete/', DocumentTypeDeleteAPI.as_view(), name='document-type-delete'),
    
    # VisaType endpoints
    path('visa-types/', VisaTypeListAPI.as_view(), name='visa-type-list'),
    path('visa-types/create/', VisaTypeCreateAPI.as_view(), name='visa-type-create'),
    path('visa-types/<uuid:id>/', VisaTypeDetailAPI.as_view(), name='visa-type-detail'),
    path('visa-types/<uuid:id>/update/', VisaTypeUpdateAPI.as_view(), name='visa-type-update'),
    path('visa-types/<uuid:id>/delete/', VisaTypeDeleteAPI.as_view(), name='visa-type-delete'),
    
    # VisaRuleVersion endpoints
    path('visa-rule-versions/', VisaRuleVersionListAPI.as_view(), name='visa-rule-version-list'),
    path('visa-rule-versions/create/', VisaRuleVersionCreateAPI.as_view(), name='visa-rule-version-create'),
    path('visa-rule-versions/<uuid:id>/', VisaRuleVersionDetailAPI.as_view(), name='visa-rule-version-detail'),
    path('visa-rule-versions/<uuid:id>/update/', VisaRuleVersionUpdateAPI.as_view(), name='visa-rule-version-update'),
    path('visa-rule-versions/<uuid:id>/delete/', VisaRuleVersionDeleteAPI.as_view(), name='visa-rule-version-delete'),
    
    # VisaRequirement endpoints
    path('visa-requirements/', VisaRequirementListAPI.as_view(), name='visa-requirement-list'),
    path('visa-requirements/create/', VisaRequirementCreateAPI.as_view(), name='visa-requirement-create'),
    path('visa-requirements/<uuid:id>/', VisaRequirementDetailAPI.as_view(), name='visa-requirement-detail'),
    path('visa-requirements/<uuid:id>/update/', VisaRequirementUpdateAPI.as_view(), name='visa-requirement-update'),
    path('visa-requirements/<uuid:id>/delete/', VisaRequirementDeleteAPI.as_view(), name='visa-requirement-delete'),
    
    # VisaDocumentRequirement endpoints
    path('visa-document-requirements/', VisaDocumentRequirementListAPI.as_view(), name='visa-document-requirement-list'),
    path('visa-document-requirements/create/', VisaDocumentRequirementCreateAPI.as_view(), name='visa-document-requirement-create'),
    path('visa-document-requirements/<uuid:id>/', VisaDocumentRequirementDetailAPI.as_view(), name='visa-document-requirement-detail'),
    path('visa-document-requirements/<uuid:id>/update/', VisaDocumentRequirementUpdateAPI.as_view(), name='visa-document-requirement-update'),
    path('visa-document-requirements/<uuid:id>/delete/', VisaDocumentRequirementDeleteAPI.as_view(), name='visa-document-requirement-delete'),
    
    # Admin endpoints (staff/superuser only)
    # DocumentType Admin
    path('admin/document-types/', DocumentTypeAdminListAPI.as_view(), name='admin-document-types-list'),
    path('admin/document-types/bulk-operation/', BulkDocumentTypeOperationAPI.as_view(), name='admin-document-types-bulk-operation'),
    path('admin/document-types/<uuid:id>/', DocumentTypeAdminDetailAPI.as_view(), name='admin-document-types-detail'),
    path('admin/document-types/<uuid:id>/activate/', DocumentTypeAdminActivateAPI.as_view(), name='admin-document-types-activate'),
    path('admin/document-types/<uuid:id>/delete/', DocumentTypeAdminDeleteAPI.as_view(), name='admin-document-types-delete'),
    
    # VisaType Admin
    path('admin/visa-types/', VisaTypeAdminListAPI.as_view(), name='admin-visa-types-list'),
    path('admin/visa-types/bulk-operation/', BulkVisaTypeOperationAPI.as_view(), name='admin-visa-types-bulk-operation'),
    path('admin/visa-types/<uuid:id>/', VisaTypeAdminDetailAPI.as_view(), name='admin-visa-types-detail'),
    path('admin/visa-types/<uuid:id>/activate/', VisaTypeAdminActivateAPI.as_view(), name='admin-visa-types-activate'),
    path('admin/visa-types/<uuid:id>/delete/', VisaTypeAdminDeleteAPI.as_view(), name='admin-visa-types-delete'),
    
    # VisaRuleVersion Admin
    path('admin/visa-rule-versions/', VisaRuleVersionAdminListAPI.as_view(), name='admin-visa-rule-versions-list'),
    path('admin/visa-rule-versions/bulk-operation/', BulkVisaRuleVersionOperationAPI.as_view(), name='admin-visa-rule-versions-bulk-operation'),
    path('admin/visa-rule-versions/<uuid:id>/', VisaRuleVersionAdminDetailAPI.as_view(), name='admin-visa-rule-versions-detail'),
    path('admin/visa-rule-versions/<uuid:id>/update/', VisaRuleVersionAdminUpdateAPI.as_view(), name='admin-visa-rule-versions-update'),
    path('admin/visa-rule-versions/<uuid:id>/publish/', VisaRuleVersionAdminPublishAPI.as_view(), name='admin-visa-rule-versions-publish'),
    path('admin/visa-rule-versions/<uuid:id>/delete/', VisaRuleVersionAdminDeleteAPI.as_view(), name='admin-visa-rule-versions-delete'),
    
    # VisaRequirement Admin
    path('admin/visa-requirements/', VisaRequirementAdminListAPI.as_view(), name='admin-visa-requirements-list'),
    path('admin/visa-requirements/bulk-operation/', BulkVisaRequirementOperationAPI.as_view(), name='admin-visa-requirements-bulk-operation'),
    path('admin/visa-requirements/<uuid:id>/', VisaRequirementAdminDetailAPI.as_view(), name='admin-visa-requirements-detail'),
    path('admin/visa-requirements/<uuid:id>/update/', VisaRequirementAdminUpdateAPI.as_view(), name='admin-visa-requirements-update'),
    path('admin/visa-requirements/<uuid:id>/delete/', VisaRequirementAdminDeleteAPI.as_view(), name='admin-visa-requirements-delete'),
    
    # VisaDocumentRequirement Admin
    path('admin/visa-document-requirements/', VisaDocumentRequirementAdminListAPI.as_view(), name='admin-visa-document-requirements-list'),
    path('admin/visa-document-requirements/bulk-operation/', BulkVisaDocumentRequirementOperationAPI.as_view(), name='admin-visa-document-requirements-bulk-operation'),
    path('admin/visa-document-requirements/<uuid:id>/', VisaDocumentRequirementAdminDetailAPI.as_view(), name='admin-visa-document-requirements-detail'),
    path('admin/visa-document-requirements/<uuid:id>/update/', VisaDocumentRequirementAdminUpdateAPI.as_view(), name='admin-visa-document-requirements-update'),
    path('admin/visa-document-requirements/<uuid:id>/delete/', VisaDocumentRequirementAdminDeleteAPI.as_view(), name='admin-visa-document-requirements-delete'),
    
    # Analytics & Statistics
    path('admin/statistics/', RulesKnowledgeStatisticsAPI.as_view(), name='admin-statistics'),
]

