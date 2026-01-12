"""
Case Ownership Mixin

Mixin class for permissions that need to check case ownership.
Provides common methods for checking case access.
"""
from .role_checker import RoleChecker


class CaseOwnershipMixin:
    """
    Mixin class for permissions that need to check case ownership.
    Provides common methods for checking case access.
    """
    
    @staticmethod
    def has_case_access(user, case):
        """
        Check if user has access to a case.
        
        Rules:
        - User owns the case (case.user == user)
        - User is superadmin
        - User is staff
        - User is reviewer (for assigned cases)
        """
        if not case:
            return False
        
        # Superadmin/Staff can access all cases
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # User owns case
        if hasattr(case, 'user') and case.user == user:
            return True
        
        return False
    
    @staticmethod
    def has_case_write_access(user, case):
        """
        Check if user has write access to a case.
        
        Rules:
        - User owns the case
        - User is superadmin
        - User is staff
        """
        if not case:
            return False
        
        # Superadmin/Staff can write to all cases
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # User owns case
        if hasattr(case, 'user') and case.user == user:
            return True
        
        return False
    
    @staticmethod
    def is_reviewer_assigned_to_case(user, case):
        """
        Check if reviewer is assigned to any review for the case.
        """
        if not case or not RoleChecker.is_reviewer(user):
            return False
        
        if hasattr(case, 'reviews'):
            assigned_reviews = case.reviews.filter(reviewer=user)
            return assigned_reviews.exists()
        
        return False
