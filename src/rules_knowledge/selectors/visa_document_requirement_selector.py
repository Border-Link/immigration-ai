from rules_knowledge.models.visa_document_requirement import VisaDocumentRequirement
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.document_type import DocumentType


class VisaDocumentRequirementSelector:
    """Selector for VisaDocumentRequirement read operations."""

    @staticmethod
    def get_all():
        """Get all document requirements."""
        return VisaDocumentRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type',
            'document_type'
        ).all().order_by('document_type__code')

    @staticmethod
    def get_by_rule_version(rule_version: VisaRuleVersion):
        """Get document requirements by rule version."""
        return VisaDocumentRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type',
            'document_type'
        ).filter(rule_version=rule_version).order_by('document_type__code')

    @staticmethod
    def get_mandatory_by_rule_version(rule_version: VisaRuleVersion):
        """Get mandatory document requirements by rule version."""
        return VisaDocumentRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type',
            'document_type'
        ).filter(rule_version=rule_version, mandatory=True).order_by('document_type__code')

    @staticmethod
    def get_by_document_type(document_type: DocumentType):
        """Get document requirements by document type."""
        return VisaDocumentRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type',
            'document_type'
        ).filter(document_type=document_type)

    @staticmethod
    def get_by_id(requirement_id):
        """Get document requirement by ID."""
        return VisaDocumentRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type',
            'document_type'
        ).get(id=requirement_id)

    @staticmethod
    def get_by_filters(rule_version_id=None, document_type_id=None, mandatory=None, visa_type_id=None, jurisdiction=None, date_from=None, date_to=None):
        """Get document requirements with advanced filtering for admin."""
        queryset = VisaDocumentRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type',
            'document_type'
        ).all()
        
        if rule_version_id:
            queryset = queryset.filter(rule_version_id=rule_version_id)
        
        if document_type_id:
            queryset = queryset.filter(document_type_id=document_type_id)
        
        if mandatory is not None:
            queryset = queryset.filter(mandatory=mandatory)
        
        if visa_type_id:
            queryset = queryset.filter(rule_version__visa_type_id=visa_type_id)
        
        if jurisdiction:
            queryset = queryset.filter(rule_version__visa_type__jurisdiction=jurisdiction)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('document_type__code')
