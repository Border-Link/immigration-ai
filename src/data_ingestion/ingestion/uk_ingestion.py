import json
import logging
import time
from typing import Dict, Optional, List
from django.conf import settings
from external_services.request import ExternalHTTPClient
from .base_ingestion import BaseIngestionSystem

UK_GOV_BASE = "https://www.gov.uk"

logger = logging.getLogger('django')


class UKIngestionSystem(BaseIngestionSystem):
    """
    Optimized UK-specific ingestion system for gov.uk API.
    Efficiently fetches and stores all endpoint data including nested child taxons.
    """

    def __init__(self, data_source):
        super().__init__(data_source)
        # Use settings key or fallback to default
        uk_api_url = getattr(settings, 'UK_GOV_API_BASE_URL', None)
        if uk_api_url:
            # Extract base domain from full URL if needed
            if '/api/content/' in uk_api_url:
                self.api_base = uk_api_url.rsplit('/api/content/', 1)[0]
            else:
                self.api_base = uk_api_url
        else:
            # Fallback to default if not configured
            self.api_base = UK_GOV_BASE
            if getattr(settings, "APP_ENV", None) != "test":
                logger.warning("UK_GOV_API_BASE_URL not set in settings, using default: https://www.gov.uk")
        
        # Use external services HTTP client
        self.client = ExternalHTTPClient(base_url=self.api_base, default_timeout=30)
        self.headers = {
            'User-Agent': 'ImmigrationIntelligenceBot/1.0',
            'Accept': 'application/json'
        }

    def fetch_content(self, url: str) -> Optional[Dict]:
        """
        Fetch content from gov.uk API.
        
        Args:
            url: Full API URL or endpoint path
            
        Returns:
            Dict with 'content', 'content_type', 'status_code', 'error'
        """
        # Extract endpoint from full URL
        endpoint = url.replace(self.api_base, '') if url.startswith('http') else url
        
        try:
            # Use external services client (returns detailed response)
            result = self.client.get(
                endpoint=endpoint,
                headers=self.headers,
                timeout=30,
                return_details=True  # Get detailed response with status_code, error, etc.
            )
            return result
        except Exception as e:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.error(f"Error fetching {url}: {e}")
            return {'error': str(e), 'content': None, 'content_type': None, 'status_code': None}

    def extract_text(self, raw_content: str, content_type: str) -> str:
        """
        Extract comprehensive text from JSON API response for hashing.
        Extracts all relevant fields that could contain rule information.
        
        Args:
            raw_content: Raw JSON content as string
            content_type: Content type
            
        Returns:
            Extracted text content for hashing
        """
        try:
            data = json.loads(raw_content)
            parts = []
            
            # Core identification fields
            if data.get('title'):
                parts.append(f"Title: {data['title']}")
            
            if data.get('description'):
                parts.append(f"Description: {data['description']}")
            
            # Details section (important for internal structure)
            if 'details' in data and isinstance(data['details'], dict):
                if data['details'].get('internal_name'):
                    parts.append(f"Internal Name: {data['details']['internal_name']}")
            
            # Path and URL information
            if data.get('base_path'):
                parts.append(f"Path: {data['base_path']}")
            
            if data.get('web_url'):
                parts.append(f"Web URL: {data['web_url']}")
            
            # Content identification
            if data.get('content_id'):
                parts.append(f"Content ID: {data['content_id']}")
            
            # Document type and schema
            if data.get('document_type'):
                parts.append(f"Document Type: {data['document_type']}")
            
            if data.get('schema_name'):
                parts.append(f"Schema: {data['schema_name']}")
            
            # Dates (important for change detection)
            if data.get('first_published_at'):
                parts.append(f"First Published: {data['first_published_at']}")
            
            if data.get('public_updated_at'):
                parts.append(f"Last Updated: {data['public_updated_at']}")
            
            # Phase and status
            if data.get('phase'):
                parts.append(f"Phase: {data['phase']}")
            
            # Locale
            if data.get('locale'):
                parts.append(f"Locale: {data['locale']}")
            
            # Extract text from child taxons (for comprehensive coverage)
            if 'links' in data and isinstance(data['links'], dict):
                # Extract titles from child taxons
                child_taxons = data['links'].get('child_taxons', [])
                if child_taxons:
                    child_titles = [child.get('title') for child in child_taxons if child.get('title')]
                    if child_titles:
                        parts.append(f"Child Taxons: {', '.join(child_titles)}")
                
                # Extract parent taxon titles
                parent_taxons = data['links'].get('parent_taxons', [])
                if parent_taxons:
                    parent_titles = [parent.get('title') for parent in parent_taxons if parent.get('title')]
                    if parent_titles:
                        parts.append(f"Parent Taxons: {', '.join(parent_titles)}")
            
            # Join all parts with newlines for better structure
            return '\n'.join(filter(None, parts))
            
        except json.JSONDecodeError:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.warning("Failed to parse JSON, returning raw content for hashing")
            return raw_content
        except Exception as e:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.error(f"Error extracting text from JSON: {e}")
            return raw_content
    
    def extract_metadata(self, raw_content: str) -> dict:
        """
        Extract structured metadata from JSON API response.
        Stores important fields in DocumentVersion.metadata for querying.
        
        Args:
            raw_content: Raw JSON content as string
            
        Returns:
            Dictionary of metadata fields
        """
        try:
            data = json.loads(raw_content)
            metadata = {}
            
            # Core identification
            if data.get('content_id'):
                metadata['content_id'] = data['content_id']
            
            if data.get('base_path'):
                metadata['base_path'] = data['base_path']
            
            if data.get('web_url'):
                metadata['web_url'] = data['web_url']
            
            # Document information
            if data.get('document_type'):
                metadata['document_type'] = data['document_type']
            
            if data.get('schema_name'):
                metadata['schema_name'] = data['schema_name']
            
            # Dates
            if data.get('first_published_at'):
                metadata['first_published_at'] = data['first_published_at']
            
            if data.get('public_updated_at'):
                metadata['public_updated_at'] = data['public_updated_at']
            
            # Status
            if data.get('phase'):
                metadata['phase'] = data['phase']
            
            if 'withdrawn' in data:
                metadata['withdrawn'] = data['withdrawn']
            
            if data.get('locale'):
                metadata['locale'] = data['locale']
            
            # Details
            if 'details' in data and isinstance(data['details'], dict):
                details_meta = {}
                if data['details'].get('internal_name'):
                    details_meta['internal_name'] = data['details']['internal_name']
                if details_meta:
                    metadata['details'] = details_meta
            
            # Links structure (for navigation)
            if 'links' in data and isinstance(data['links'], dict):
                links_meta = {}
                
                # Child taxon IDs and paths
                child_taxons = data['links'].get('child_taxons', [])
                if child_taxons:
                    links_meta['child_taxons'] = [
                        {
                            'content_id': child.get('content_id'),
                            'api_url': child.get('api_url'),
                            'base_path': child.get('base_path'),
                            'title': child.get('title')
                        }
                        for child in child_taxons
                        if child.get('content_id')
                    ]
                
                # Parent taxon IDs and paths
                parent_taxons = data['links'].get('parent_taxons', [])
                if parent_taxons:
                    links_meta['parent_taxons'] = [
                        {
                            'content_id': parent.get('content_id'),
                            'api_url': parent.get('api_url'),
                            'base_path': parent.get('base_path'),
                            'title': parent.get('title')
                        }
                        for parent in parent_taxons
                        if parent.get('content_id')
                    ]
                
                if links_meta:
                    metadata['links'] = links_meta
            
            return metadata
            
        except json.JSONDecodeError:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.warning("Failed to parse JSON for metadata extraction")
            return {}
        except Exception as e:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.error(f"Error extracting metadata from JSON: {e}")
            return {}

    def parse_api_response(self, response: Dict) -> List[str]:
        """
        Extract child taxon URLs from Content API response.
        Also extracts content_id for later Search API queries.
        
        Args:
            response: API response as dictionary
            
        Returns:
            List of child taxon API URLs
        """
        urls = []
        if 'links' in response and isinstance(response['links'], dict):
            child_taxons = response['links'].get('child_taxons', [])
            for child in child_taxons:
                # Only process active, non-withdrawn taxons
                if not child.get('withdrawn', False) and child.get('api_url'):
                    urls.append(child['api_url'])
        return urls
    
    def get_content_pages_by_taxon(self, taxon_content_id: str) -> List[str]:
        """
        Use Search API to find all content pages tagged to a taxon.
        This fetches actual content pages, not just taxon metadata.
        
        Args:
            taxon_content_id: Content ID of the taxon (from Content API)
            
        Returns:
            List of content page API URLs
        """
        content_urls = []
        page = 1
        max_pages = 100  # Safety limit
        
        while page <= max_pages:
            try:
                # Search API endpoint
                endpoint = f"/api/search.json?filter_taxons={taxon_content_id}&count=50&page={page}"
                
                result = self.client.get_with_details(
                    endpoint=endpoint,
                    headers=self.headers,
                    timeout=30
                )
                
                if not result or not result.get('content'):
                    break
                
                data = json.loads(result['content'])
                results = data.get('results', [])
                
                if not results:
                    break
                
                # Extract content page URLs from search results
                for item in results:
                    base_path = item.get('base_path')
                    if base_path:
                        # Convert to Content API URL
                        content_url = f"{self.api_base}/api/content{base_path}"
                        content_urls.append(content_url)
                
                # Check if there are more pages
                total_results = data.get('total', 0)
                current_count = len(results)
                
                if page * 50 >= total_results or current_count < 50:
                    break
                
                page += 1
                time.sleep(1)  # Rate limiting for search API
                
            except json.JSONDecodeError as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.warning(f"Invalid JSON from search API for taxon {taxon_content_id}, page {page}: {e}")
                break
            except Exception as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.error(f"Error fetching search results for taxon {taxon_content_id}, page {page}: {e}")
                break
        
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Found {len(content_urls)} content pages for taxon {taxon_content_id}")
        return content_urls

    def get_document_urls(self) -> List[str]:
        """
        Discover all URLs using both Content API (for taxons) and Search API (for content pages).
        
        Process:
        1. Use Content API to discover taxon hierarchy
        2. For each taxon, use Search API to find actual content pages
        3. Fetch all content pages
        
        Returns:
            List of all URLs to fetch (taxons + content pages)
        """
        urls = []
        visited = set()
        taxon_content_ids = []  # Store taxon IDs for Search API queries
        
        # Use data_source.base_url or settings key, with fallback
        base_url = self.data_source.base_url
        if not base_url:
            # Try to get from settings
            uk_api_url = getattr(settings, 'UK_GOV_API_BASE_URL', None)
            if uk_api_url:
                base_url = uk_api_url
            else:
                # Final fallback
                base_url = f"{self.api_base}/api/content/entering-staying-uk"
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.warning(f"Using fallback base URL: {base_url}")
        
        errors = []
        
        def fetch_taxons_recursive(url: str, depth: int = 0, max_depth: int = 15):
            """
            Recursively fetch taxon structure from Content API.
            Collects taxon content_ids for later Search API queries.
            """
            # Safety checks
            if depth > max_depth:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.warning(f"Max depth reached for {url}")
                return
            
            if url in visited:
                return
            
            visited.add(url)
            urls.append(url)  # Add taxon URL to fetch list
            
            # Rate limiting: 2 seconds between requests
            if len(urls) > 1:
                time.sleep(2)
            
            # Fetch the taxon from Content API
            response = self.fetch_content(url)
            
            if not response:
                errors.append(f"Failed to fetch {url}: No response")
                return
            
            if response.get('error'):
                errors.append(f"Error fetching {url}: {response.get('error')}")
                return
            
            if not response.get('content'):
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.warning(f"No content returned for {url}")
                return
            
            # Parse response and extract child taxon URLs
            try:
                data = json.loads(response['content'])
                
                # Extract content_id for Search API
                content_id = data.get('content_id')
                if content_id:
                    taxon_content_ids.append(content_id)
                
                # Extract child taxon URLs
                child_urls = self.parse_api_response(data)
                
                # Recursively process child taxons
                for child_url in child_urls:
                    if child_url not in visited:
                        fetch_taxons_recursive(child_url, depth + 1, max_depth)
                        
            except json.JSONDecodeError as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.warning(f"Invalid JSON response from {url}: {e}")
                errors.append(f"JSON decode error for {url}: {e}")
            except KeyError as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.warning(f"Missing key in response from {url}: {e}")
                errors.append(f"Key error for {url}: {e}")
            except Exception as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.error(f"Unexpected error processing {url}: {e}")
                errors.append(f"Unexpected error for {url}: {e}")
        
        # Step 1: Discover taxon hierarchy using Content API
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Step 1: Discovering taxon hierarchy from {base_url}")
        fetch_taxons_recursive(base_url)
        
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(
                f"Taxon discovery complete: {len(urls)} taxons found, {len(taxon_content_ids)} taxon IDs collected"
            )
        
        # Step 2: Use Search API to find actual content pages for each taxon
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Step 2: Discovering content pages using Search API for {len(taxon_content_ids)} taxons")
        content_pages_found = 0
        
        for taxon_id in taxon_content_ids:
            try:
                content_page_urls = self.get_content_pages_by_taxon(taxon_id)
                for content_url in content_page_urls:
                    if content_url not in visited:
                        visited.add(content_url)
                        urls.append(content_url)
                        content_pages_found += 1
            except Exception as e:
                if getattr(settings, "APP_ENV", None) != "test":
                    logger.error(f"Error fetching content pages for taxon {taxon_id}: {e}")
                errors.append(f"Error fetching content for taxon {taxon_id}: {e}")
        
        # Log final results
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(
                f"URL discovery complete: {len(urls)} total URLs found "
                f"({len(taxon_content_ids)} taxons + {content_pages_found} content pages), "
                f"{len(errors)} errors"
            )
        
        if errors:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.warning(f"Errors during URL discovery: {errors[:5]}...")  # Log first 5 errors
        
        return urls
