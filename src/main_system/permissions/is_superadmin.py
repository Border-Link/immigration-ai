from rest_framework import permissions
from main_system.permissions.role_checker import RoleChecker


class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow superadmin users.
    
    According to ROLE_TO_IMPLEMENT.md:
    - Super Admin: role == 'superadmin'
    
    Implementation:
    - is_superuser=True OR (role='admin' AND is_superuser=True)
    (since the User model uses is_superuser flag and role='admin' for admin users)
    """
    
    def has_permission(self, request, view):
        """Check if user is superuser (superadmin)."""
        user = getattr(request, 'user', None)
        return RoleChecker.is_superadmin(user)
