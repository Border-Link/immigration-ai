from rest_framework import permissions
from main_system.permissions.role_checker import RoleChecker


class IsStaff(permissions.BasePermission):
    """
    Custom permission to allow staff and superadmin users.
    
    According to ROLE_TO_IMPLEMENT.md:
    - Staff: role in ['staff', 'superadmin']
    
    Implementation:
    - is_staff=True OR is_superuser=True OR role='admin'
    (since the User model uses role='admin' for admin users and is_staff/is_superuser flags)
    """
    
    def has_permission(self, request, view):
        """Check if user is staff or superuser."""
        user = getattr(request, 'user', None)
        return RoleChecker.is_staff(user)
