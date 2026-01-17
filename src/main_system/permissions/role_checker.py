"""
Role Checker Utility Class

Utility class for checking user roles.
All role checks are class-based static methods.
"""
from django.contrib.auth.models import AnonymousUser


class RoleChecker:
    """
    Utility class for checking user roles.
    All role checks are class-based static methods.
    """
    
    @staticmethod
    def _is_authenticated_user(user):
        """
        Helper method to check if user is authenticated.
        Handles both regular User objects and AnonymousUser.
        """
        if user is None:
            return False
        if isinstance(user, AnonymousUser):
            return False
        # Check if user has is_authenticated attribute (Django user model)
        # In Django, is_authenticated is a boolean property (not callable in modern Django)
        try:
            # Try to access is_authenticated as a property
            is_auth = getattr(user, 'is_authenticated', False)
            # In Django 3.1+, is_authenticated is a boolean property
            # In older versions, it might be a callable
            if callable(is_auth):
                return bool(is_auth())
            return bool(is_auth)
        except (AttributeError, TypeError):
            # If we can't access is_authenticated, assume not authenticated
            return False
    
    @staticmethod
    def is_superadmin(user):
        """Check if user is superadmin."""
        if not RoleChecker._is_authenticated_user(user):
            return False
        return getattr(user, 'is_superuser', False)
    
    @staticmethod
    def is_staff(user):
        """Check if user is staff or superadmin."""
        if not RoleChecker._is_authenticated_user(user):
            return False
        if getattr(user, 'is_superuser', False):
            return True
        if getattr(user, 'is_staff', False):
            return True
        if getattr(user, 'role', None) == 'admin':
            return True
        return False
    
    @staticmethod
    def is_reviewer(user):
        """Check if user is reviewer, staff, or superadmin."""
        if not RoleChecker._is_authenticated_user(user):
            return False
        if getattr(user, 'is_superuser', False):
            return True
        if getattr(user, 'is_staff', False):
            return True
        if getattr(user, 'role', None) == 'admin':
            return True
        if getattr(user, 'role', None) == 'reviewer' and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
            return True
        return False
    
    @staticmethod
    def is_user(user):
        """Check if user is authenticated (any role)."""
        return RoleChecker._is_authenticated_user(user)
