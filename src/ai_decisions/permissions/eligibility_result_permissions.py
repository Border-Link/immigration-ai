"""
Permission classes for Eligibility Result access control.

These permissions are specific to the ai_decisions module and provide
clear, self-documenting access control for eligibility results.
"""
from rest_framework import permissions
from main_system.permissions.case_ownership import CaseOwnershipPermission


class CanViewEligibilityResult(permissions.BasePermission):
    """
    Permission to view eligibility results.
    
    Rules:
    - User owns the case (case.user == user)
    - User is superuser
    - User is reviewer (role='reviewer' AND is_staff/is_superuser)
    - User is admin (role='admin' OR is_staff)
    
    Usage:
        permission_classes = [CanViewEligibilityResult]
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has access to the eligibility result's case.
        
        The object should be an EligibilityResult instance with a 'case' attribute.
        """
        if not hasattr(obj, 'case'):
            return False
        
        return CaseOwnershipPermission.has_case_access(request.user, obj.case)


class CanModifyEligibilityResult(permissions.BasePermission):
    """
    Permission to modify (update/delete) eligibility results.
    
    Rules:
    - User owns the case (case.user == user)
    - User is superuser
    - User is admin (role='admin' OR is_staff)
    
    Note: Reviewers do NOT have write access (read-only).
    
    Usage:
        permission_classes = [CanModifyEligibilityResult]
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has write access to the eligibility result's case.
        
        The object should be an EligibilityResult instance with a 'case' attribute.
        """
        if not hasattr(obj, 'case'):
            return False
        
        return CaseOwnershipPermission.has_case_write_access(request.user, obj.case)
