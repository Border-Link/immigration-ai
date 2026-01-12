from rest_framework import permissions
from main_system.permissions.case_ownership import CaseOwnershipPermission


class HasCaseOwnership(permissions.BasePermission):
    """
    DRF permission class to check if user has access to a case.
    
    This permission checks case ownership for eligibility results and other case-related resources.
    It extracts the case from the resource (e.g., eligibility_result.case) and verifies access.
    
    Usage:
        permission_classes = [HasCaseOwnership]
    
    The view should have a method to get the resource, and the resource should have a 'case' attribute.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has access to the object's case.
        
        The object should have a 'case' attribute (e.g., EligibilityResult.case).
        """
        if not hasattr(obj, 'case'):
            # If object doesn't have a case attribute, deny access
            return False
        
        return CaseOwnershipPermission.has_case_access(request.user, obj.case)


class HasCaseWriteAccess(permissions.BasePermission):
    """
    DRF permission class to check if user has write access to a case.
    
    This permission checks case write access for eligibility results and other case-related resources.
    Reviewers have read-only access by default.
    
    Usage:
        permission_classes = [HasCaseWriteAccess]
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has write access to the object's case.
        
        The object should have a 'case' attribute (e.g., EligibilityResult.case).
        """
        if not hasattr(obj, 'case'):
            # If object doesn't have a case attribute, deny access
            return False
        
        return CaseOwnershipPermission.has_case_write_access(request.user, obj.case)
