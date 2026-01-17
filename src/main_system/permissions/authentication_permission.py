"""
Authentication Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Register, login, reset password
- Reviewer: Login
- Staff: Login, create users
- Super Admin: Full user management (CRUD users, assign roles)
"""
from .base_permissions import BaseModulePermission
from .role_checker import RoleChecker


class AuthenticationPermission(BaseModulePermission):
    """
    Authentication Module Permissions
    
    Object-level: Users can manage their own account.
    Staff/Superadmin can manage any account.
    """

    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user

        if request.method == 'POST' and 'login' in view.__class__.__name__.lower():
            return True

        if request.method == 'POST' and 'register' in view.__class__.__name__.lower():
            return True

        if request.method == 'POST' and 'password' in view.__class__.__name__.lower():
            return True

        return bool(user and user.is_authenticated)


    def has_object_permission(self, request, view, obj):
        """Object-level permission: Users can manage their own account."""
        user = request.user
    
        # Staff/Superadmin can manage any account
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True

        # Users can manage their own account
        if hasattr(obj, 'id') and obj.id == user.id:
            return True

        return False
