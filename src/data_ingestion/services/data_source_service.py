import logging
from main_system.utils.cache_utils import invalidate_cache
from main_system.utils.cache_utils import cache_result
from data_ingestion.models.data_source import DataSource
from data_ingestion.repositories.data_source_repository import DataSourceRepository
from data_ingestion.selectors.data_source_selector import DataSourceSelector

logger = logging.getLogger('django')

def namespace(*args, **kwargs) -> str:
    # Single namespace to invalidate all data source caches on any write.
    return "ns:data_ingestion:data_sources"


class DataSourceService:
    """Service for DataSource business logic."""

    @staticmethod
    @invalidate_cache(namespace)
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
    @cache_result(timeout=1800, keys=[], namespace=namespace)  # 30 minutes
    def get_all():
        """Get all data sources."""
        try:
            return DataSourceSelector.get_all()
        except Exception as e:
            logger.error(f"Error fetching all data sources: {e}")
            return DataSourceSelector.get_none()

    @staticmethod
    @cache_result(timeout=1800, keys=[], namespace=namespace)  # 30 minutes
    def get_active():
        """Get all active data sources."""
        try:
            return DataSourceSelector.get_active()
        except Exception as e:
            logger.error(f"Error fetching active data sources: {e}")
            return DataSourceSelector.get_none()

    @staticmethod
    @cache_result(timeout=1800, keys=['jurisdiction'], namespace=namespace)  # 30 minutes
    def get_by_jurisdiction(jurisdiction: str):
        """Get data sources by jurisdiction."""
        try:
            return DataSourceSelector.get_by_jurisdiction(jurisdiction)
        except Exception as e:
            logger.error(f"Error fetching data sources for jurisdiction {jurisdiction}: {e}")
            return DataSourceSelector.get_none()

    @staticmethod
    @cache_result(timeout=3600, keys=['data_source_id'], namespace=namespace)  # 1 hour
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
    @invalidate_cache(namespace)
    def update_data_source(data_source, **fields):
        """Update data source fields."""
        try:
            return DataSourceRepository.update_data_source(data_source, **fields)
        except Exception as e:
            logger.error(f"Error updating data source {data_source.id}: {e}")
            return None

    @staticmethod
    @invalidate_cache(namespace)
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

    @staticmethod
    @invalidate_cache(namespace)
    def delete_data_source(data_source_id: str) -> bool:
        """Delete a data source."""
        try:
            data_source = DataSourceSelector.get_by_id(data_source_id)
            if not data_source:
                logger.error(f"Data source {data_source_id} not found")
                return False
            DataSourceRepository.delete_data_source(data_source)
            return True
        except Exception as e:
            logger.error(f"Error deleting data source {data_source_id}: {e}")
            return False

    @staticmethod
    def get_by_filters(jurisdiction: str = None, is_active: bool = None, date_from=None, date_to=None):
        """Get data sources with filters."""
        try:
            return DataSourceSelector.get_by_filters(
                jurisdiction=jurisdiction,
                is_active=is_active,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            logger.error(f"Error fetching filtered data sources: {e}")
            return DataSourceSelector.get_none()

    @staticmethod
    @cache_result(timeout=60, keys=[], namespace=namespace, user_scope="global")
    def get_statistics():
        """Get data source statistics."""
        try:
            return DataSourceSelector.get_statistics()
        except Exception as e:
            logger.error(f"Error getting data source statistics: {e}")
            return {}
