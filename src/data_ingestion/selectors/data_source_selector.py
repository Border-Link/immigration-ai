from data_ingestion.models.data_source import DataSource


class DataSourceSelector:
    """Selector for DataSource read operations."""

    @staticmethod
    def get_all():
        """Get all data sources."""
        return DataSource.objects.all()

    @staticmethod
    def get_active():
        """Get all active data sources."""
        return DataSource.objects.filter(is_active=True)

    @staticmethod
    def get_by_jurisdiction(jurisdiction: str):
        """Get data sources by jurisdiction."""
        return DataSource.objects.filter(jurisdiction=jurisdiction, is_active=True)

    @staticmethod
    def get_by_id(data_source_id):
        """Get data source by ID."""
        return DataSource.objects.get(id=data_source_id)

    @staticmethod
    def get_by_base_url(base_url: str):
        """Get data source by base URL."""
        return DataSource.objects.filter(base_url=base_url).first()

    @staticmethod
    def get_none():
        """Get empty queryset."""
        return DataSource.objects.none()

    @staticmethod
    def get_by_filters(jurisdiction: str = None, is_active: bool = None, date_from=None, date_to=None):
        """Get data sources with filters."""
        queryset = DataSource.objects.all()
        
        if jurisdiction:
            queryset = queryset.filter(jurisdiction=jurisdiction)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset

    @staticmethod
    def get_statistics():
        """Get data source statistics."""
        from django.db.models import Count
        
        queryset = DataSource.objects.all()
        
        total_sources = queryset.count()
        active_sources = queryset.filter(is_active=True).count()
        sources_by_jurisdiction = queryset.values('jurisdiction').annotate(
            count=Count('id')
        ).order_by('jurisdiction')
        
        return {
            'total': total_sources,
            'active': active_sources,
            'inactive': total_sources - active_sources,
            'by_jurisdiction': list(sources_by_jurisdiction),
        }
