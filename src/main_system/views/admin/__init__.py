"""
Admin Views Base Classes

Base classes for admin views to reduce code duplication.
"""

from .base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminActivateAPI,
    BaseAdminUpdateAPI,
)

from .bulk_operation import BaseBulkOperationAPI

__all__ = [
    'BaseAdminDetailAPI',
    'BaseAdminDeleteAPI',
    'BaseAdminActivateAPI',
    'BaseAdminUpdateAPI',
    'BaseBulkOperationAPI',
]
