from rules_knowledge.models.document_type import DocumentType


class DocumentTypeSelector:
    """Selector for DocumentType read operations."""

    @staticmethod
    def get_all():
        """Get all document types."""
        return DocumentType.objects.all().order_by('code')

    @staticmethod
    def get_active():
        """Get all active document types."""
        return DocumentType.objects.filter(is_active=True).order_by('code')

    @staticmethod
    def get_all_active():
        """Get all active document types (alias for get_active)."""
        return DocumentTypeSelector.get_active()

    @staticmethod
    def get_by_code(code: str):
        """Get document type by code."""
        return DocumentType.objects.get(code=code)

    @staticmethod
    def get_by_id(type_id):
        """Get document type by ID."""
        return DocumentType.objects.get(id=type_id)

    @staticmethod
    def get_by_filters(is_active=None, code=None, date_from=None, date_to=None):
        """Get document types with advanced filtering for admin."""
        queryset = DocumentType.objects.all()
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        
        if code:
            queryset = queryset.filter(code__icontains=code)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('code')
