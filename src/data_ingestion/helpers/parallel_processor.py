"""
Parallel and streaming processing utilities for rule parsing.

Provides async/parallel processing capabilities for batch operations.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings

logger = logging.getLogger('django')

# Default thread pool size
DEFAULT_MAX_WORKERS = getattr(settings, 'RULE_PARSING_MAX_WORKERS', 3)


class ParallelProcessor:
    """
    Parallel processing utilities for rule parsing operations.
    """
    
    @staticmethod
    def process_in_parallel(
        items: List[Any],
        process_func: Callable,
        max_workers: Optional[int] = None,
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process items in parallel using thread pool.
        
        Args:
            items: List of items to process
            process_func: Function to process each item (must be thread-safe)
            max_workers: Maximum number of worker threads
            continue_on_error: Whether to continue on errors
            
        Returns:
            List of results (one per item)
        """
        max_workers = max_workers or DEFAULT_MAX_WORKERS
        results = []
        
        logger.info(f"Processing {len(items)} items in parallel with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_func, item): item
                for item in items
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append({
                        'item': item,
                        'result': result,
                        'success': True,
                        'error': None
                    })
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}", exc_info=True)
                    results.append({
                        'item': item,
                        'result': None,
                        'success': False,
                        'error': str(e)
                    })
                    if not continue_on_error:
                        # Cancel remaining tasks
                        for f in future_to_item:
                            f.cancel()
                        break
        
        return results
    
    @staticmethod
    async def process_async(
        items: List[Any],
        process_func: Callable,
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process items asynchronously.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of results
        """
        max_concurrent = max_concurrent or DEFAULT_MAX_WORKERS
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(item):
            async with semaphore:
                try:
                    result = await process_func(item)
                    return {
                        'item': item,
                        'result': result,
                        'success': True,
                        'error': None
                    }
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}", exc_info=True)
                    return {
                        'item': item,
                        'result': None,
                        'success': False,
                        'error': str(e)
                    }
        
        # Process all items concurrently
        tasks = [process_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks)
        
        return results


class StreamingProcessor:
    """
    Streaming processor for large documents.
    
    Processes documents in chunks to handle large content efficiently.
    """
    
    @staticmethod
    def process_in_chunks(
        text: str,
        chunk_size: int = 4000,
        overlap: int = 200,
        process_chunk_func: Callable = None
    ) -> List[Dict[str, Any]]:
        """
        Process text in overlapping chunks.
        
        Args:
            text: Text to process
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            process_chunk_func: Function to process each chunk
            
        Returns:
            List of chunk processing results
        """
        if not process_chunk_func:
            # Default: just return chunks
            def default_func(chunk):
                return {'chunk': chunk, 'length': len(chunk)}
            process_chunk_func = default_func
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk = text[start:end]
            
            # Process chunk
            result = process_chunk_func(chunk)
            result['start'] = start
            result['end'] = end
            chunks.append(result)
            
            # Move to next chunk with overlap
            start = end - overlap
            if start >= text_length:
                break
        
        logger.info(f"Processed text into {len(chunks)} chunks")
        return chunks
    
    @staticmethod
    def merge_chunk_results(chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge results from multiple chunks.
        
        Args:
            chunk_results: List of chunk processing results
            
        Returns:
            Merged result dictionary
        """
        merged = {
            'total_chunks': len(chunk_results),
            'rules': [],
            'tokens_used': 0,
            'estimated_cost': 0.0,
        }
        
        # Aggregate results
        for chunk_result in chunk_results:
            if chunk_result.get('rules'):
                merged['rules'].extend(chunk_result['rules'])
            if chunk_result.get('tokens_used'):
                merged['tokens_used'] += chunk_result['tokens_used']
            if chunk_result.get('estimated_cost'):
                merged['estimated_cost'] += chunk_result['estimated_cost']
        
        # Deduplicate rules (simple: by requirement_code and description)
        seen = set()
        unique_rules = []
        for rule in merged['rules']:
            key = (rule.get('requirement_code'), rule.get('description'))
            if key not in seen:
                seen.add(key)
                unique_rules.append(rule)
        
        merged['rules'] = unique_rules
        merged['unique_rules_count'] = len(unique_rules)
        
        return merged
