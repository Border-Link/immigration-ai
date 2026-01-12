"""
Base Permission Classes and Common Utilities

Provides base classes and role checking utilities used across all module permissions.
All utilities are class-based for consistency.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS

class BaseModulePermission(BasePermission):
    """
    Base permission class for all module permissions.
    Provides common functionality and structure.
    """
    
    def has_permission(self, request, view):
        """
        Module-level permission check.
        Override in subclasses.
        """
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Override in subclasses.
        """
        return False
