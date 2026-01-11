"""
Pagination helper for all list endpoints.

Provides simple pagination functionality following system patterns.
Unified implementation used across all modules.
"""
from typing import Tuple
from django.core.paginator import Paginator
from django.db.models import QuerySet


def paginate_queryset(queryset: QuerySet, page: int = 1, page_size: int = 20) -> Tuple[list, dict]:
    """
    Paginate a queryset and return paginated results with metadata.
    
    Args:
        queryset: Django QuerySet to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        
    Returns:
        Tuple of (paginated_items, pagination_metadata)
    """
    # Validate and sanitize inputs
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    try:
        page_size = int(page_size)
        if page_size < 1:
            page_size = 20
        if page_size > 100:  # Max page size to prevent abuse
            page_size = 100
    except (ValueError, TypeError):
        page_size = 20
    
    # Create paginator
    paginator = Paginator(queryset, page_size)
    
    # Get total count
    total_count = paginator.count
    total_pages = paginator.num_pages
    
    # Get requested page
    try:
        page_obj = paginator.page(page)
        items = list(page_obj.object_list)
    except Exception:
        # If page is out of range, return empty list
        items = []
        page = 1
    
    # Build pagination metadata
    pagination_metadata = {
        'page': page,
        'page_size': page_size,
        'total_count': total_count,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
    }
    
    return items, pagination_metadata
