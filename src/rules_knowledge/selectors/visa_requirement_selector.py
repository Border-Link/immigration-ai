from rules_knowledge.models.visa_requirement import VisaRequirement
from rules_knowledge.models.visa_rule_version import VisaRuleVersion


class VisaRequirementSelector:
    """Selector for VisaRequirement read operations."""

    @staticmethod
    def get_all():
        """Get all requirements."""
        return VisaRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type'
        ).all().order_by('requirement_code')

    @staticmethod
    def get_by_rule_version(rule_version: VisaRuleVersion):
        """Get requirements by rule version."""
        return VisaRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type'
        ).filter(rule_version=rule_version).order_by('requirement_code')

    @staticmethod
    def get_mandatory_by_rule_version(rule_version: VisaRuleVersion):
        """Get mandatory requirements by rule version."""
        return VisaRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type'
        ).filter(rule_version=rule_version, is_mandatory=True).order_by('requirement_code')

    @staticmethod
    def get_by_rule_type(rule_type: str):
        """Get requirements by rule type."""
        return VisaRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type'
        ).filter(rule_type=rule_type).order_by('requirement_code')

    @staticmethod
    def get_by_id(requirement_id):
        """Get requirement by ID."""
        return VisaRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type'
        ).get(id=requirement_id)

    @staticmethod
    def get_by_filters(rule_version_id=None, rule_type=None, is_mandatory=None, requirement_code=None, visa_type_id=None, jurisdiction=None, date_from=None, date_to=None):
        """Get requirements with advanced filtering for admin."""
        queryset = VisaRequirement.objects.select_related(
            'rule_version',
            'rule_version__visa_type'
        ).all()
        
        if rule_version_id:
            queryset = queryset.filter(rule_version_id=rule_version_id)
        
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        
        if is_mandatory is not None:
            queryset = queryset.filter(is_mandatory=is_mandatory)
        
        if requirement_code:
            queryset = queryset.filter(requirement_code__icontains=requirement_code)
        
        if visa_type_id:
            queryset = queryset.filter(rule_version__visa_type_id=visa_type_id)
        
        if jurisdiction:
            queryset = queryset.filter(rule_version__visa_type__jurisdiction=jurisdiction)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('requirement_code')
