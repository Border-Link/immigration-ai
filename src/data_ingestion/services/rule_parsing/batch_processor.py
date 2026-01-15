"""
Batch processing utilities for rule parsing.

Handles parallel and batch processing of multiple document versions.
"""

import logging
from typing import Dict, List, Optional, Any
from data_ingestion.models.document_version import DocumentVersion
from data_ingestion.helpers.parallel_processor import ParallelProcessor
from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
from data_ingestion.selectors.parsed_rule_selector import ParsedRuleSelector
from django.conf import settings

logger = logging.getLogger('django')


class BatchProcessor:
    """Handles batch processing of document versions."""
    
    @staticmethod
    def parse_document_versions_batch(
        document_versions: List[DocumentVersion],
        max_concurrent: int = 3,
        continue_on_error: bool = True,
        use_parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Parse multiple document versions in batch with parallel processing.
        
        Args:
            document_versions: List of DocumentVersion instances to parse
            max_concurrent: Maximum concurrent parsing operations
            continue_on_error: Whether to continue processing on errors
            use_parallel: Whether to use parallel processing (default: True)
            
        Returns:
            Dict with:
            - total: Total documents
            - successful: Number successfully parsed
            - failed: Number failed
            - skipped: Number skipped (already parsed)
            - results: List of individual results
            - summary: Summary statistics
        """
        from .service import RuleParsingService
        
        total = len(document_versions)
        
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Starting batch parsing for {total} document versions (parallel={use_parallel}, workers={max_concurrent})")
        
        if use_parallel and total > 1:
            # Use parallel processing
            def process_doc(doc_version):
                """Process a single document version."""
                try:
                    result = RuleParsingService.parse_document_version(doc_version)
                    result['document_version_id'] = str(doc_version.id)
                    return result
                except Exception as e:
                    if getattr(settings, "APP_ENV", None) != "test":
                        logger.error(f"Error processing document version {doc_version.id}: {e}", exc_info=True)
                    return {
                        'document_version_id': str(doc_version.id),
                        'success': False,
                        'error': str(e),
                        'error_type': 'UnexpectedError'
                    }
            
            # Process in parallel
            parallel_results = ParallelProcessor.process_in_parallel(
                items=document_versions,
                process_func=process_doc,
                max_workers=max_concurrent,
                continue_on_error=continue_on_error
            )
            
            # Extract results
            results = [r['result'] for r in parallel_results if r['result']]
            
            # Add indices
            for idx, result in enumerate(results, 1):
                result['index'] = idx
        else:
            # Sequential processing (fallback or for single item)
            results = []
            for idx, doc_version in enumerate(document_versions, 1):
                try:
                    if getattr(settings, "APP_ENV", None) != "test":
                        logger.info(f"Processing document {idx}/{total}: {doc_version.id}")
                    
                    result = RuleParsingService.parse_document_version(doc_version)
                    result['document_version_id'] = str(doc_version.id)
                    result['index'] = idx
                    results.append(result)
                    
                    if not result.get('success') and not continue_on_error:
                        if getattr(settings, "APP_ENV", None) != "test":
                            logger.error(f"Stopping batch processing due to error in document {doc_version.id}")
                        break
                        
                except Exception as e:
                    if getattr(settings, "APP_ENV", None) != "test":
                        logger.error(f"Error processing document version {doc_version.id}: {e}", exc_info=True)
                    results.append({
                        'document_version_id': str(doc_version.id),
                        'index': idx,
                        'success': False,
                        'error': str(e),
                        'error_type': 'UnexpectedError'
                    })
                    if not continue_on_error:
                        break
        
        # Calculate statistics
        successful = sum(1 for r in results if r.get('success') and r.get('message') != 'Already parsed')
        failed = sum(1 for r in results if not r.get('success'))
        skipped = sum(1 for r in results if r.get('success') and r.get('message') == 'Already parsed')
        
        total_rules = sum(r.get('rules_created', 0) for r in results if r.get('success'))
        total_tokens = sum(r.get('tokens_used', 0) or 0 for r in results if r.get('success'))
        total_cost = sum(r.get('estimated_cost', 0) or 0 for r in results if r.get('success'))
        successful_results = [r for r in results if r.get('success') and r.get('message') != 'Already parsed']
        avg_processing_time = sum(
            r.get('processing_time_ms', 0) for r in successful_results
        ) / max(len(successful_results), 1)
        
        summary = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'total_rules_created': total_rules,
            'total_tokens_used': total_tokens,
            'total_estimated_cost': round(total_cost, 6),
            'average_processing_time_ms': round(avg_processing_time, 2),
            'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
            'parallel_processing': use_parallel
        }
        
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(
                f"Batch parsing completed: {successful} successful, {failed} failed, "
                f"{skipped} skipped out of {total} total"
            )
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'results': results,
            'summary': summary
        }
    
    @staticmethod
    def parse_document_versions_by_ids(
        document_version_ids: List[str],
        max_concurrent: int = 3,
        continue_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Parse document versions by their IDs.
        
        Args:
            document_version_ids: List of document version UUIDs
            max_concurrent: Maximum concurrent parsing operations
            continue_on_error: Whether to continue processing on errors
            
        Returns:
            Dict with batch processing results
        """
        from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
        
        document_versions = []
        for doc_id in document_version_ids:
            try:
                doc_version = DocumentVersionSelector.get_by_id(doc_id)
                document_versions.append(doc_version)
            except Exception as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.error(f"Error fetching document version {doc_id}: {e}")
                if not continue_on_error:
                    return {
                        'total': len(document_version_ids),
                        'successful': 0,
                        'failed': len(document_version_ids),
                        'skipped': 0,
                        'results': [],
                        'summary': {'error': f'Failed to fetch document versions: {str(e)}'}
                    }
        
        return BatchProcessor.parse_document_versions_batch(
            document_versions=document_versions,
            max_concurrent=max_concurrent,
            continue_on_error=continue_on_error
        )
    
    @staticmethod
    def parse_pending_document_versions(
        limit: Optional[int] = None,
        jurisdiction: Optional[str] = None,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Parse pending document versions that haven't been parsed yet.
        
        Args:
            limit: Maximum number of documents to process (None for all)
            jurisdiction: Optional jurisdiction filter
            max_concurrent: Maximum concurrent parsing operations
            
        Returns:
            Dict with batch processing results
        """
        from data_ingestion.selectors.document_version_selector import DocumentVersionSelector
        
        # Get document versions
        if jurisdiction:
            document_versions = DocumentVersionSelector.get_by_jurisdiction(jurisdiction)
        else:
            document_versions = DocumentVersionSelector.get_all()
        
        # Filter out already parsed versions
        pending_versions = []
        for doc_version in document_versions:
            existing_rules = ParsedRuleSelector.get_by_document_version(doc_version)
            if not existing_rules.exists():
                pending_versions.append(doc_version)
                if limit and len(pending_versions) >= limit:
                    break
        
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Found {len(pending_versions)} pending document versions to parse")
        
        return BatchProcessor.parse_document_versions_batch(
            document_versions=pending_versions,
            max_concurrent=max_concurrent,
            continue_on_error=True
        )
