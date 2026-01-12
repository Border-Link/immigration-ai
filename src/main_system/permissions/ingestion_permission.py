"""
Ingestion Service Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: No access
- Reviewer: No access
- Staff: Monitor ingestion status
- Super Admin: Full ingestion service management (scheduler, rule parsing, publishing)
"""
from .base_permissions import BaseModulePermission
from .role_checker import RoleChecker


class IngestionPermission(BaseModulePermission):
    """
    Ingestion Service Module Permissions
    
    Object-level: Based on assignment or superadmin access.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # Only staff and superadmin can access ingestion service
        return RoleChecker.is_staff(user)
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on assignment or superadmin access."""
        user = request.user
        
        # Superadmin can access all ingestion tasks
        if RoleChecker.is_superadmin(user):
            return True
        
        # Staff can access assigned ingestion tasks
        if RoleChecker.is_staff(user):
            # Check if task is assigned to this staff member
            if hasattr(obj, 'assigned_to') and obj.assigned_to == user:
                return True
            # For rule validation tasks, staff can view all
            if hasattr(obj, 'assigned_to'):
                return True
        
        return False
