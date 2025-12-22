import logging
from data_ingestion.models.data_source import DataSource
from data_ingestion.repositories.data_source_repository import DataSourceRepository
from data_ingestion.selectors.data_source_selector import DataSourceSelector

logger = logging.getLogger('django')


class DataSourceService:
    """Service for DataSource business logic."""

    @staticmethod
    def create_data_source(name: str, base_url: str, jurisdiction: str,
                          crawl_frequency: str = 'daily', is_active: bool = True):
        """Create a new data source."""
        try:
            return DataSourceRepository.create_data_source(
                name=name,
                base_url=base_url,
                jurisdiction=jurisdiction,
                crawl_frequency=crawl_frequency,
                is_active=is_active
            )
        except Exception as e:
            logger.error(f"Error creating data source: {e}")
            return None

    @staticmethod
    def get_all():
        """Get all data sources."""
        try:
            return DataSourceSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all data sources: {e}")
            return DataSource.objects.none()

    @staticmethod
    def get_active():
        """Get all active data sources."""
        try:
            return DataSourceSelector.get_active()
        except Exception as e:
            logger.error(f"Error fetching active data sources: {e}")
            return DataSource.objects.none()

    @staticmethod
    def get_by_jurisdiction(jurisdiction: str):
        """Get data sources by jurisdiction."""
        try:
            return DataSourceSelector.get_by_jurisdiction(jurisdiction)
        except Exception as e:
            logger.error(f"Error fetching data sources for jurisdiction {jurisdiction}: {e}")
            return DataSource.objects.none()

    @staticmethod
    def get_by_id(data_source_id):
        """Get data source by ID."""
        try:
            return DataSourceSelector.get_by_id(data_source_id)
        except DataSource.DoesNotExist:
            logger.error(f"Data source {data_source_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching data source {data_source_id}: {e}")
            return None

    @staticmethod
    def update_data_source(data_source, **fields):
        """Update data source fields."""
        try:
            return DataSourceRepository.update_data_source(data_source, **fields)
        except Exception as e:
            logger.error(f"Error updating data source {data_source.id}: {e}")
            return None

    @staticmethod
    def activate_data_source(data_source, is_active: bool):
        """Activate or deactivate data source."""
        try:
            return DataSourceRepository.activate_data_source(data_source, is_active)
        except Exception as e:
            logger.error(f"Error activating/deactivating data source {data_source.id}: {e}")
            return None

    @staticmethod
    def trigger_ingestion(data_source_id: str, async_task: bool = True):
        """
        Trigger ingestion for a data source.
        
        Args:
            data_source_id: UUID of the data source
            async_task: If True, use Celery task; if False, run synchronously
            
        Returns:
            Task ID if async, or result dict if sync
        """
        try:
            from data_ingestion.services.ingestion_service import IngestionService
            if async_task:
                from data_ingestion.tasks.ingestion_tasks import ingest_data_source_task
                task = ingest_data_source_task.delay(data_source_id)
                return {'task_id': task.id, 'status': 'queued'}
            else:
                return IngestionService.ingest_data_source(data_source_id)
        except Exception as e:
            logger.error(f"Error triggering ingestion for {data_source_id}: {e}")
            return {'success': False, 'message': str(e)}

