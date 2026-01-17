from document_handling.models.document_check import DocumentCheck
from document_handling.models.case_document import CaseDocument


class DocumentCheckSelector:
    """Selector for DocumentCheck read operations."""

    @staticmethod
    def get_all():
        """Get all document checks (excluding soft-deleted)."""
        return DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_case_document(case_document: CaseDocument):
        """Get checks by case document (excluding soft-deleted)."""
        return DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(case_document=case_document, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_check_type(check_type: str):
        """Get checks by check type (excluding soft-deleted)."""
        return DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(check_type=check_type, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_result(result: str):
        """Get checks by result (excluding soft-deleted)."""
        return DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(result=result, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(check_id):
        """Get document check by ID (excluding soft-deleted)."""
        return DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(is_deleted=False).get(id=check_id)

    @staticmethod
    def get_latest_by_case_document(case_document: CaseDocument, check_type: str = None):
        """Get latest check for a case document, optionally filtered by check type."""
        queryset = DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(case_document=case_document, is_deleted=False)
        
        if check_type:
            queryset = queryset.filter(check_type=check_type)
        
        return queryset.order_by('-created_at').first()

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return DocumentCheck.objects.none()

    @staticmethod
    def get_by_filters(case_document_id: str = None, check_type: str = None, result: str = None,
                       performed_by: str = None, date_from=None, date_to=None):
        """Get document checks with filters."""
        queryset = DocumentCheck.objects.select_related(
            'case_document',
            'case_document__case',
            'case_document__document_type'
        ).filter(is_deleted=False)
        
        if case_document_id:
            queryset = queryset.filter(case_document_id=case_document_id)
        if check_type:
            queryset = queryset.filter(check_type=check_type)
        if result:
            queryset = queryset.filter(result=result)
        if performed_by:
            queryset = queryset.filter(performed_by=performed_by)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        queryset = queryset.order_by('-created_at')
        return queryset

    @staticmethod
    def get_statistics():
        """Get document check statistics."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = DocumentCheck.objects.filter(is_deleted=False)
        
        total_checks = queryset.count()
        checks_by_type = queryset.values('check_type').annotate(
            count=Count('id')
        ).order_by('check_type')
        checks_by_result = queryset.values('result').annotate(
            count=Count('id')
        ).order_by('result')
        
        # Recent activity (last 24 hours, 7 days, 30 days)
        now = timezone.now()
        last_24h = queryset.filter(created_at__gte=now - timedelta(hours=24)).count()
        last_7d = queryset.filter(created_at__gte=now - timedelta(days=7)).count()
        last_30d = queryset.filter(created_at__gte=now - timedelta(days=30)).count()
        
        # Failed checks
        failed_checks = queryset.filter(result='failed').count()
        passed_checks = queryset.filter(result='passed').count()
        warning_checks = queryset.filter(result='warning').count()
        pending_checks = queryset.filter(result='pending').count()
        
        return {
            'total': total_checks,
            'by_type': list(checks_by_type),
            'by_result': list(checks_by_result),
            'failed': failed_checks,
            'passed': passed_checks,
            'warning': warning_checks,
            'pending': pending_checks,
            'recent_activity': {
                'last_24_hours': last_24h,
                'last_7_days': last_7d,
                'last_30_days': last_30d,
            },
        }
