from rest_framework import permissions


class IsUser(permissions.BasePermission):
    """
    Custom permission to allow any authenticated user.
    
    According to ROLE_TO_IMPLEMENT.md:
    - User: Any authenticated user (user, reviewer, staff, superadmin)
    
    This is the most permissive permission - allows any authenticated user.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
