import difflib
import logging
from typing import Dict
from data_ingestion.models.data_source import DataSource
from data_ingestion.ingestion.factory import IngestionSystemFactory
from data_ingestion.repositories.data_source_repository import DataSourceRepository
from data_ingestion.repositories.source_document_repository import SourceDocumentRepository
from data_ingestion.repositories.document_version_repository import DocumentVersionRepository
from data_ingestion.repositories.document_diff_repository import DocumentDiffRepository
from data_ingestion.selectors.data_source_selector import DataSourceSelector
from data_ingestion.selectors.document_version_selector import DocumentVersionSelector

logger = logging.getLogger('django')


class IngestionService:
    """
    Main service for orchestrating the ingestion pipeline.
    Handles: Fetch → Hash → Diff → Parse → Validate
    """

    @staticmethod
    def ingest_data_source(data_source_id: str) -> Dict:
        """
        Main ingestion method for a data source.
        
        Args:
            data_source_id: UUID of the data source to ingest
            
        Returns:
            Dict with ingestion results
        """
        try:
            data_source = DataSourceSelector.get_by_id(data_source_id)
            
            if not data_source.is_active:
                logger.warning(f"Data source {data_source_id} is not active")
                return {'success': False, 'message': 'Data source is not active'}
            
            # Get the appropriate ingestion system
            ingestion_system = IngestionSystemFactory.create(data_source)
            if not ingestion_system:
                logger.error(f"Could not create ingestion system for {data_source.jurisdiction}")
                return {'success': False, 'message': f'Unsupported jurisdiction: {data_source.jurisdiction}'}
            
            # Get document URLs to fetch
            urls = ingestion_system.get_document_urls()
            
            results = {
                'success': True,
                'data_source_id': str(data_source_id),
                'urls_processed': 0,
                'new_versions': 0,
                'diffs_created': 0,
                'rules_parsed': 0,
                'validation_tasks_created': 0,
                'errors': []
            }
            
            # Process each URL
            for url in urls:
                try:
                    result = IngestionService._process_url(
                        data_source, ingestion_system, url
                    )
                    results['urls_processed'] += 1
                    if result.get('new_version'):
                        results['new_versions'] += 1
                    if result.get('diff_created'):
                        results['diffs_created'] += 1
                    if result.get('rules_parsed'):
                        results['rules_parsed'] += result.get('rules_parsed', 0)
                    if result.get('validation_tasks_created'):
                        results['validation_tasks_created'] += result.get('validation_tasks_created', 0)
                except Exception as e:
                    logger.error(f"Error processing URL {url}: {e}")
                    results['errors'].append({'url': url, 'error': str(e)})
            
            # Update last_fetched_at
            DataSourceRepository.update_last_fetched(data_source)
            
            return results
            
        except DataSource.DoesNotExist:
            logger.error(f"Data source {data_source_id} not found")
            return {'success': False, 'message': 'Data source not found'}
        except Exception as e:
            logger.error(f"Error ingesting data source {data_source_id}: {e}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def _process_url(data_source: DataSource, ingestion_system, url: str) -> Dict:
        """
        Process a single URL: fetch, extract, hash, compare, create version/diff.
        
        Args:
            data_source: DataSource instance
            ingestion_system: Ingestion system instance
            url: URL to process
            
        Returns:
            Dict with processing results
        """
        result = {
            'url': url,
            'new_version': False,
            'diff_created': False
        }
        
        # 1. Fetch content
        fetch_result = ingestion_system.fetch_content(url)
        if not fetch_result or fetch_result.get('error'):
            result['error'] = fetch_result.get('error', 'Unknown fetch error')
            return result
        
        # 2. Create source document
        source_doc = SourceDocumentRepository.create_source_document(
            data_source=data_source,
            source_url=url,
            raw_content=fetch_result['content'],
            content_type=fetch_result['content_type'],
            http_status_code=fetch_result['status_code']
        )
        
        # 3. Extract text
        extracted_text = ingestion_system.extract_text(
            fetch_result['content'],
            fetch_result['content_type']
        )
        
        # 4. Compute hash
        from helpers.file_hashing import ContentHash
        content_hash = ContentHash.compute_sha256(extracted_text)
        
        # 5. Check if version already exists for this source document
        # We check by source_document to ensure each URL maintains its own version history
        existing_versions = DocumentVersionSelector.get_by_source_document(source_doc)
        for existing_version in existing_versions:
            if existing_version.content_hash == content_hash:
                logger.info(f"Content unchanged for {url}, hash: {content_hash[:8]}...")
                return result
        
        # 6. Create new document version
        new_version = DocumentVersionRepository.create_document_version(
            source_document=source_doc,
            raw_text=extracted_text
        )
        result['new_version'] = True
        
        # 7. Get previous version for diff
        previous_version = DocumentVersionSelector.get_latest_by_source_document(source_doc)
        change_detected = False
        change_type = None
        
        if previous_version and previous_version.id != new_version.id:
            # 8. Create diff
            diff_text = IngestionService._compute_diff(
                previous_version.raw_text,
                new_version.raw_text
            )
            
            change_type = IngestionService._classify_change(diff_text)
            
            DocumentDiffRepository.create_document_diff(
                old_version=previous_version,
                new_version=new_version,
                diff_text=diff_text,
                change_type=change_type
            )
            result['diff_created'] = True
            change_detected = True
        
        # 9. Trigger AI Rule Parsing (as per implementation.md flow)
        # Parse rules for new document versions (especially when change is detected)
        if new_version:
            try:
                from data_ingestion.services.rule_parsing_service import RuleParsingService
                parse_result = RuleParsingService.parse_document_version(new_version)
                result['rules_parsed'] = parse_result.get('rules_created', 0)
                result['validation_tasks_created'] = parse_result.get('validation_tasks_created', 0)
            except Exception as e:
                logger.error(f"Error triggering rule parsing for {url}: {e}")
                result['parsing_error'] = str(e)
        
        return result

    @staticmethod
    def _compute_diff(old_text: str, new_text: str) -> str:
        """
        Compute unified diff between two text versions.
        
        Args:
            old_text: Previous version text
            new_text: New version text
            
        Returns:
            Unified diff string
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='old_version',
            tofile='new_version',
            lineterm=''
        )
        
        return ''.join(diff)

    @staticmethod
    def _classify_change(diff_text: str) -> str:
        """
        Classify the type of change detected.
        
        Args:
            diff_text: Diff text to analyze
            
        Returns:
            Change type classification
        """
        diff_lower = diff_text.lower()
        
        # Check for requirement changes (salary, threshold, etc.)
        requirement_keywords = ['salary', 'threshold', 'minimum', 'requirement', 'must', 'need']
        if any(keyword in diff_lower for keyword in requirement_keywords):
            # Check for numeric patterns
            import re
            if re.search(r'[£$€]\s*\d+|\d+\s*(pound|dollar|euro)', diff_lower):
                return 'requirement_change'
        
        # Check for fee changes
        fee_keywords = ['fee', 'cost', 'charge', 'payment']
        if any(keyword in diff_lower for keyword in fee_keywords):
            import re
            if re.search(r'[£$€]\s*\d+|\d+\s*(pound|dollar|euro)', diff_lower):
                return 'fee_change'
        
        # Check for processing time changes
        time_keywords = ['day', 'week', 'month', 'processing', 'time', 'duration']
        if any(keyword in diff_lower for keyword in time_keywords):
            import re
            if re.search(r'\d+\s*(day|week|month|hour)', diff_lower):
                return 'processing_time_change'
        
        # Check for major updates (large diff)
        if len(diff_text) > 10000:
            return 'major_update'
        
        # Default to minor text change
        return 'minor_text'

