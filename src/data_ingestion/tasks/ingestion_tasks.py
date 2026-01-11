from celery import shared_task
import logging
from main_system.utils.tasks_base import BaseTaskWithMeta
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
def ingest_uk_sources_weekly_task(self):
    """
    Celery task to ingest UK data sources weekly.
    Optimized for weekly schedule - processes all active UK sources.
    Runs every Sunday at 2 AM UTC via Celery Beat.
    
    Returns:
        Dict with results for UK sources
    """
    try:
        from data_ingestion.selectors.data_source_selector import DataSourceSelector
        
        logger.info("Starting weekly UK ingestion task")
        uk_sources = DataSourceSelector.get_by_jurisdiction('UK').filter(is_active=True)
        
        results = {
            'jurisdiction': 'UK',
            'total_sources': uk_sources.count(),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'urls_processed': 0,
            'new_versions': 0,
            'rules_parsed': 0,
            'details': []
        }
        
        for source in uk_sources:
            try:
                logger.info(f"Processing UK source: {source.name} ({source.id})")
                result = IngestionService.ingest_data_source(str(source.id))
                results['processed'] += 1
                
                if result.get('success'):
                    results['successful'] += 1
                    results['urls_processed'] += result.get('urls_processed', 0)
                    results['new_versions'] += result.get('new_versions', 0)
                    results['rules_parsed'] += result.get('rules_parsed', 0)
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'data_source_id': str(source.id),
                    'name': source.name,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error ingesting UK source {source.id}: {e}", exc_info=True)
                results['failed'] += 1
                results['details'].append({
                    'data_source_id': str(source.id),
                    'name': source.name,
                    'error': str(e)
                })
        
        logger.info(
            f"Weekly UK ingestion completed: {results['successful']}/{results['total_sources']} successful, "
            f"{results['urls_processed']} URLs processed, {results['new_versions']} new versions, "
            f"{results['rules_parsed']} rules parsed"
        )
        return results
        
    except Exception as e:
        logger.error(f"Error in weekly UK ingestion task: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300, max_retries=3)


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

