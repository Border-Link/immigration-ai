from document_handling.models.case_document import CaseDocument
from immigration_cases.models.case import Case


class CaseDocumentSelector:
    """Selector for CaseDocument read operations."""

    @staticmethod
    def get_all():
        """Get all case documents (excluding soft-deleted)."""
        return CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(is_deleted=False).order_by('-uploaded_at')

    @staticmethod
    def get_by_case(case: Case):
        """Get documents by case (excluding soft-deleted)."""
        return CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(case=case, is_deleted=False).order_by('-uploaded_at')

    @staticmethod
    def get_by_status(status: str):
        """Get documents by status (excluding soft-deleted)."""
        return CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(status=status, is_deleted=False).order_by('-uploaded_at')

    @staticmethod
    def get_by_document_type(document_type_id):
        """Get documents by document type (excluding soft-deleted)."""
        return CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(document_type_id=document_type_id, is_deleted=False).order_by('-uploaded_at')

    @staticmethod
    def get_by_id(document_id):
        """Get case document by ID (excluding soft-deleted)."""
        return CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(is_deleted=False).get(id=document_id)

    @staticmethod
    def get_verified_by_case(case: Case):
        """Get verified documents by case (excluding soft-deleted)."""
        return CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(case=case, status='verified', is_deleted=False).order_by('-uploaded_at')

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return CaseDocument.objects.none()

    @staticmethod
    def get_by_filters(case_id: str = None, document_type_id: str = None, status: str = None,
                       has_ocr_text: bool = None, min_confidence: float = None,
                       date_from=None, date_to=None, mime_type: str = None,
                       has_expiry_date: bool = None, expiry_date_from=None, expiry_date_to=None,
                       content_validation_status: str = None, is_expired: bool = None):
        """Get case documents with filters."""
        from django.db.models import Q
        from django.utils import timezone
        from datetime import date
        
        queryset = CaseDocument.objects.select_related(
            'case',
            'case__user',
            'document_type'
        ).filter(is_deleted=False)
        
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        if document_type_id:
            queryset = queryset.filter(document_type_id=document_type_id)
        if status:
            queryset = queryset.filter(status=status)
        if has_ocr_text is not None:
            if has_ocr_text:
                queryset = queryset.exclude(ocr_text__isnull=True).exclude(ocr_text='')
            else:
                queryset = queryset.filter(Q(ocr_text__isnull=True) | Q(ocr_text=''))
        if min_confidence is not None:
            queryset = queryset.filter(classification_confidence__gte=min_confidence)
        if mime_type:
            queryset = queryset.filter(mime_type=mime_type)
        if date_from:
            queryset = queryset.filter(uploaded_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(uploaded_at__lte=date_to)
        if has_expiry_date is not None:
            if has_expiry_date:
                queryset = queryset.exclude(expiry_date__isnull=True)
            else:
                queryset = queryset.filter(expiry_date__isnull=True)
        if expiry_date_from:
            queryset = queryset.filter(expiry_date__gte=expiry_date_from)
        if expiry_date_to:
            queryset = queryset.filter(expiry_date__lte=expiry_date_to)
        if content_validation_status:
            queryset = queryset.filter(content_validation_status=content_validation_status)
        if is_expired is not None:
            today = date.today()
            if is_expired:
                queryset = queryset.filter(expiry_date__lt=today)
            else:
                queryset = queryset.filter(Q(expiry_date__gte=today) | Q(expiry_date__isnull=True))
        
        queryset = queryset.order_by('-uploaded_at')
        return queryset

    @staticmethod
    def get_statistics():
        """Get case document statistics."""
        from django.db.models import Count, Avg, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = CaseDocument.objects.filter(is_deleted=False)
        
        total_documents = queryset.count()
        documents_by_status = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        documents_with_ocr = queryset.exclude(ocr_text__isnull=True).exclude(ocr_text='').count()
        documents_without_ocr = queryset.filter(ocr_text__isnull=True) | queryset.filter(ocr_text='')
        documents_without_ocr = documents_without_ocr.count()
        
        avg_confidence = queryset.exclude(classification_confidence__isnull=True).aggregate(
            avg=Avg('classification_confidence')
        )['avg'] or 0.0
        
        total_file_size = queryset.aggregate(
            total=Sum('file_size')
        )['total'] or 0
        
        # Recent activity (last 24 hours, 7 days, 30 days)
        now = timezone.now()
        last_24h = queryset.filter(uploaded_at__gte=now - timedelta(hours=24)).count()
        last_7d = queryset.filter(uploaded_at__gte=now - timedelta(days=7)).count()
        last_30d = queryset.filter(uploaded_at__gte=now - timedelta(days=30)).count()
        
        # Documents by document type (top 10)
        by_document_type = queryset.values('document_type__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Expiry date statistics
        documents_with_expiry = queryset.exclude(expiry_date__isnull=True).count()
        expired_documents = queryset.exclude(expiry_date__isnull=True).filter(
            expiry_date__lt=timezone.now().date()
        ).count()
        expiring_soon = queryset.exclude(expiry_date__isnull=True).filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=timezone.now().date() + timedelta(days=90)
        ).count()
        
        # Content validation statistics
        by_validation_status = queryset.values('content_validation_status').annotate(
            count=Count('id')
        ).order_by('content_validation_status')
        validation_passed = queryset.filter(content_validation_status='passed').count()
        validation_failed = queryset.filter(content_validation_status='failed').count()
        validation_warning = queryset.filter(content_validation_status='warning').count()
        
        return {
            'total': total_documents,
            'by_status': list(documents_by_status),
            'with_ocr': documents_with_ocr,
            'without_ocr': documents_without_ocr,
            'average_classification_confidence': round(avg_confidence, 3),
            'total_file_size_bytes': total_file_size,
            'total_file_size_mb': round(total_file_size / (1024 * 1024), 2) if total_file_size > 0 else 0,
            'recent_activity': {
                'last_24_hours': last_24h,
                'last_7_days': last_7d,
                'last_30_days': last_30d,
            },
            'by_document_type': [
                {'document_type': item['document_type__name'] or 'Unknown', 'count': item['count']}
                for item in by_document_type
            ],
            'expiry_statistics': {
                'with_expiry_date': documents_with_expiry,
                'expired': expired_documents,
                'expiring_soon': expiring_soon,
            },
            'content_validation': {
                'by_status': list(by_validation_status),
                'passed': validation_passed,
                'failed': validation_failed,
                'warning': validation_warning,
            },
        }
