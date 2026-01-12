"""
Rule Validation Task Permission

According to ROLE_TO_IMPLEMENT.md:
- Staff: Monitor ingestion status (includes rule validation tasks)
- Super Admin: Full ingestion service management

Reviewers can access tasks assigned to them.
"""
from .base_permissions import BaseModulePermission
from .role_checker import RoleChecker


class RuleValidationTaskPermission(BaseModulePermission):
    """
    Rule Validation Task Permissions
    
    Staff can monitor ingestion status (includes rule validation tasks).
    Super Admin has full ingestion service management.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # Only staff and superadmin can access rule validation tasks
        return RoleChecker.is_staff(user)
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on assignment or superadmin access."""
        user = request.user
        
        # Superadmin can access all tasks
        if RoleChecker.is_superadmin(user):
            return True
        
        # Staff can access assigned tasks or all tasks
        if RoleChecker.is_staff(user):
            if hasattr(obj, 'assigned_to'):
                # If assigned, check if assigned to this user
                if obj.assigned_to == user:
                    return True
                # Staff can view all tasks
                return True
            return True
        
        return False
