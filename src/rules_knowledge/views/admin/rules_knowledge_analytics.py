"""
Admin API Views for Rules Knowledge Analytics and Statistics

Admin-only endpoints for rules knowledge analytics, statistics, and reporting.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from rules_knowledge.services.document_type_service import DocumentTypeService
from rules_knowledge.services.visa_type_service import VisaTypeService
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from rules_knowledge.services.visa_requirement_service import VisaRequirementService
from rules_knowledge.services.visa_document_requirement_service import VisaDocumentRequirementService
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger('django')


class RulesKnowledgeStatisticsAPI(AuthAPI):
    """
    Admin: Get rules knowledge statistics and analytics.
    
    Endpoint: GET /api/v1/rules-knowledge/admin/statistics/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        try:
            from rules_knowledge.models.document_type import DocumentType
            from rules_knowledge.models.visa_type import VisaType
            from rules_knowledge.models.visa_rule_version import VisaRuleVersion
            from rules_knowledge.models.visa_requirement import VisaRequirement
            from rules_knowledge.models.visa_document_requirement import VisaDocumentRequirement
            
            # Document Types Statistics
            document_type_total = DocumentType.objects.count()
            document_type_active = DocumentType.objects.filter(is_active=True).count()
            document_type_inactive = DocumentType.objects.filter(is_active=False).count()
            
            # Visa Types Statistics
            visa_type_total = VisaType.objects.count()
            visa_type_active = VisaType.objects.filter(is_active=True).count()
            visa_type_inactive = VisaType.objects.filter(is_active=False).count()
            visa_type_by_jurisdiction = list(
                VisaType.objects.values('jurisdiction')
                .annotate(count=Count('id'))
                .order_by('jurisdiction')
            )
            
            # Visa Rule Versions Statistics
            rule_version_total = VisaRuleVersion.objects.count()
            rule_version_published = VisaRuleVersion.objects.filter(is_published=True).count()
            rule_version_unpublished = VisaRuleVersion.objects.filter(is_published=False).count()
            now = timezone.now()
            rule_version_current = VisaRuleVersion.objects.filter(
                effective_from__lte=now,
                is_published=True
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=now)
            ).count()
            
            # Visa Requirements Statistics
            requirement_total = VisaRequirement.objects.count()
            requirement_mandatory = VisaRequirement.objects.filter(is_mandatory=True).count()
            requirement_optional = VisaRequirement.objects.filter(is_mandatory=False).count()
            requirement_by_type = list(
                VisaRequirement.objects.values('rule_type')
                .annotate(count=Count('id'))
                .order_by('rule_type')
            )
            
            # Visa Document Requirements Statistics
            doc_requirement_total = VisaDocumentRequirement.objects.count()
            doc_requirement_mandatory = VisaDocumentRequirement.objects.filter(mandatory=True).count()
            doc_requirement_optional = VisaDocumentRequirement.objects.filter(mandatory=False).count()
            
            statistics = {
                'document_types': {
                    'total': document_type_total,
                    'active': document_type_active,
                    'inactive': document_type_inactive,
                },
                'visa_types': {
                    'total': visa_type_total,
                    'active': visa_type_active,
                    'inactive': visa_type_inactive,
                    'by_jurisdiction': visa_type_by_jurisdiction,
                },
                'visa_rule_versions': {
                    'total': rule_version_total,
                    'published': rule_version_published,
                    'unpublished': rule_version_unpublished,
                    'current': rule_version_current,
                },
                'visa_requirements': {
                    'total': requirement_total,
                    'mandatory': requirement_mandatory,
                    'optional': requirement_optional,
                    'by_type': requirement_by_type,
                },
                'visa_document_requirements': {
                    'total': doc_requirement_total,
                    'mandatory': doc_requirement_mandatory,
                    'optional': doc_requirement_optional,
                },
            }
            
            return self.api_response(
                message="Rules knowledge statistics retrieved successfully.",
                data=statistics,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving rules knowledge statistics: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving rules knowledge statistics.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
