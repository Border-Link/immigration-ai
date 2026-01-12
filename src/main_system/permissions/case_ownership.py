"""
Case Ownership Permission Helper

Utility functions for checking case ownership and permissions.
Used across views to ensure users can only access their own cases (unless reviewer/admin).
"""
from typing import Optional
from django.contrib.auth import get_user_model
from immigration_cases.models.case import Case

User = get_user_model()


class CaseOwnershipPermission:
    """
    Helper class for case ownership and permission checks.
    """
    
    @staticmethod
    def has_case_access(user, case: Optional[Case]) -> bool:
        """
        Check if user has access to a case.
        
        Rules:
        - User owns the case (case.user == user)
        - User is superuser
        - User is reviewer (role='reviewer' AND is_staff/is_superuser)
        - User is admin (role='admin' OR is_staff)
        
        Args:
            user: User instance
            case: Case instance (can be None)
            
        Returns:
            True if user has access, False otherwise
        """
        if not case:
            return False
        
        # User owns case
        if case.user == user:
            return True
        
        # User is superuser
        if user.is_superuser:
            return True
        
        # User is admin (role='admin' OR is_staff)
        if user.role == 'admin' or user.is_staff:
            return True
        
        # User is reviewer (must be staff or superuser per IsReviewer permission)
        if user.role == 'reviewer' and (user.is_staff or user.is_superuser):
            return True
        
        return False
    
    @staticmethod
    def has_case_write_access(user, case: Optional[Case]) -> bool:
        """
        Check if user has write access to a case.
        
        Rules:
        - User owns the case (case.user == user)
        - User is superuser
        - User is admin (role='admin' OR is_staff)
        
        Reviewers typically have read-only access unless explicitly granted.
        
        Args:
            user: User instance
            case: Case instance (can be None)
            
        Returns:
            True if user has write access, False otherwise
        """
        if not case:
            return False
        
        # User owns case
        if case.user == user:
            return True
        
        # User is superuser
        if user.is_superuser:
            return True
        
        # User is admin (role='admin' OR is_staff)
        if user.role == 'admin' or user.is_staff:
            return True
        
        # Reviewers don't have write access by default
        return False
    
    @staticmethod
    def filter_cases_by_access(user, cases):
        """
        Filter queryset of cases to only include cases user has access to.
        
        Args:
            user: User instance
            cases: QuerySet of Case objects
            
        Returns:
            Filtered QuerySet
        """
        from django.db.models import Q
        
        # Build query: user owns case OR user is admin/reviewer/superuser
        query = Q(user=user)
        
        # If user is admin/reviewer/superuser, they can see all cases
        if user.is_superuser or user.is_staff or user.role in ['admin', 'reviewer']:
            return cases
        
        # Otherwise, only their own cases
        return cases.filter(query)
