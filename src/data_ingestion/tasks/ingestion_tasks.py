from celery import shared_task
import logging
from main_system.tasks_base import BaseTaskWithMeta
from data_ingestion.services.ingestion_service import IngestionService

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def ingest_data_source_task(self, data_source_id: str):
    """
    Celery task to ingest a data source.
    
    Args:
        data_source_id: UUID of the data source to ingest
        
    Returns:
        Dict with ingestion results
    """
    try:
        logger.info(f"Starting ingestion task for data source: {data_source_id}")
        result = IngestionService.ingest_data_source(data_source_id)
        logger.info(f"Ingestion task completed for data source: {data_source_id}")
        return result
    except Exception as e:
        logger.error(f"Error in ingestion task for data source {data_source_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, base=BaseTaskWithMeta)
def ingest_all_active_sources_task(self):
    """
    Celery task to ingest all active data sources.
    This is typically called by Celery Beat on a schedule.
    
    Returns:
        Dict with results for all sources
    """
    try:
        from data_ingestion.selectors.data_source_selector import DataSourceSelector
        
        logger.info("Starting ingestion task for all active data sources")
        active_sources = DataSourceSelector.get_active()
        
        results = {
            'total_sources': active_sources.count(),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for source in active_sources:
            try:
                result = IngestionService.ingest_data_source(str(source.id))
                results['processed'] += 1
                if result.get('success'):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                results['details'].append({
                    'data_source_id': str(source.id),
                    'name': source.name,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error ingesting source {source.id}: {e}")
                results['failed'] += 1
                results['details'].append({
                    'data_source_id': str(source.id),
                    'name': source.name,
                    'error': str(e)
                })
        
        logger.info(f"Ingestion task completed: {results['successful']}/{results['total_sources']} successful")
        return results
        
    except Exception as e:
        logger.error(f"Error in bulk ingestion task: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)

