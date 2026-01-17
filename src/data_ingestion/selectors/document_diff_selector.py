from data_ingestion.models.document_diff import DocumentDiff

class DocumentDiffSelector:
    """Selector for DocumentDiff read operations."""

    @staticmethod
    def get_all():
        """Get all document diffs."""
        return DocumentDiff.objects.select_related(
            'old_version', 'new_version',
            'old_version__source_document',
            'new_version__source_document'
        ).filter(is_deleted=False)

    @staticmethod
    def get_by_versions(old_version, new_version):
        """Get diff between two versions."""
        return DocumentDiff.objects.select_related(
            'old_version', 'new_version',
            'old_version__source_document',
            'new_version__source_document'
        ).filter(old_version=old_version, new_version=new_version, is_deleted=False).first()

    @staticmethod
    def get_by_change_type(change_type: str):
        """Get diffs by change type."""
        return DocumentDiff.objects.select_related(
            'old_version', 'new_version',
            'old_version__source_document',
            'new_version__source_document'
        ).filter(change_type=change_type, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_by_id(diff_id):
        """Get document diff by ID."""
        return DocumentDiff.objects.select_related(
            'old_version', 'new_version',
            'old_version__source_document',
            'new_version__source_document'
        ).filter(id=diff_id, is_deleted=False).first()

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return DocumentDiff.objects.none()

    @staticmethod
    def get_by_filters(change_type: str = None, date_from=None, date_to=None):
        """Get document diffs with filters."""
        if change_type:
            queryset = DocumentDiffSelector.get_by_change_type(change_type)
        else:
            queryset = DocumentDiffSelector.get_all()
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
