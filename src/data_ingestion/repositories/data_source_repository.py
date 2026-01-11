from django.db import transaction
from main_system.repositories.base import BaseRepositoryMixin
from data_ingestion.models.data_source import DataSource


class DataSourceRepository:
    """Repository for DataSource write operations."""

    @staticmethod
    def create_data_source(name: str, base_url: str, jurisdiction: str, 
                          crawl_frequency: str = 'daily', is_active: bool = True):
        """Create a new data source."""
        with transaction.atomic():
            data_source = DataSource.objects.create(
                name=name,
                base_url=base_url,
                jurisdiction=jurisdiction,
                crawl_frequency=crawl_frequency,
                is_active=is_active
            )
            data_source.full_clean()
            data_source.save()
            return data_source

    @staticmethod
    def update_data_source(data_source, **fields):
        """Update data source fields."""
        return BaseRepositoryMixin.update_model_fields(
            data_source,
            **fields,
            cache_keys=[f'data_source:{data_source.id}']
        )

    @staticmethod
    def update_last_fetched(data_source):
        """Update last_fetched_at timestamp."""
        from django.utils import timezone
        with transaction.atomic():
            data_source.last_fetched_at = timezone.now()
            data_source.save(update_fields=['last_fetched_at'])
            return data_source

    @staticmethod
    def activate_data_source(data_source, is_active: bool):
        """Activate or deactivate data source."""
        with transaction.atomic():
            data_source.is_active = is_active
            data_source.full_clean()
            data_source.save()
            return data_source

    @staticmethod
    def delete_data_source(data_source):
        """Delete a data source."""
        with transaction.atomic():
            data_source.delete()
            return True
