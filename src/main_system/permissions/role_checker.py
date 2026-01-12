"""
Role Checker Utility Class

Utility class for checking user roles.
All role checks are class-based static methods.
"""


class RoleChecker:
    """
    Utility class for checking user roles.
    All role checks are class-based static methods.
    """
    
    @staticmethod
    def is_superadmin(user):
        """Check if user is superadmin."""
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser
    
    @staticmethod
    def is_staff(user):
        """Check if user is staff or superadmin."""
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.is_staff:
            return True
        if user.role == 'admin':
            return True
        return False
    
    @staticmethod
    def is_reviewer(user):
        """Check if user is reviewer, staff, or superadmin."""
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.is_staff:
            return True
        if user.role == 'admin':
            return True
        if user.role == 'reviewer' and (user.is_staff or user.is_superuser):
            return True
        return False
    
    @staticmethod
    def is_user(user):
        """Check if user is authenticated (any role)."""
        if not user or not user.is_authenticated:
            return False
        return True
