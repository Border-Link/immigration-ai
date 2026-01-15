"""
Authentication Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Register, login, reset password
- Reviewer: Login
- Staff: Login, create users
- Super Admin: Full user management (CRUD users, assign roles)
"""
from rest_framework.exceptions import NotAuthenticated
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
        
        # All authenticated users can login
        if request.method == 'POST' and 'login' in str(view.__class__).lower():
            return RoleChecker.is_user(user)
        
        # Registration is public (no auth required)
        if request.method == 'POST' and 'register' in str(view.__class__).lower():
            return True
        
        # Password reset is public (no auth required)
        if request.method == 'POST' and 'password' in str(view.__class__).lower() and 'reset' in str(view.__class__).lower():
            return True

        # Everything else requires authentication; unauth should be a 401 (not 403).
        if not user or not getattr(user, "is_authenticated", False):
            raise NotAuthenticated()

        # Default: any authenticated user is allowed for "authenticated" endpoints.
        # Staff-only endpoints should use AdminPermission explicitly.
        return True
    
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
