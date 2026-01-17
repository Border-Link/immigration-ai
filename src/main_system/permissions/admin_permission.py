"""
Admin Console Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: No access
- Reviewer: No access
- Staff: Limited admin tasks (e.g., audit logs, rule validation tasks)
- Super Admin: Full admin console access
"""
from rest_framework.exceptions import NotAuthenticated
from .base_permissions import BaseModulePermission
from .role_checker import RoleChecker


class AdminPermission(BaseModulePermission):
    """
    Admin Console Module Permissions
    
    Only staff and superadmin can access admin console.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user

        # If the request isn't authenticated, this should be a 401 (not a 403).
        if not RoleChecker.is_user(user):
            raise NotAuthenticated("Authentication credentials were not provided.")
        
        # Only staff and superadmin can access admin console
        return RoleChecker.is_staff(user)
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Same as module-level."""
        return self.has_permission(request, view)
