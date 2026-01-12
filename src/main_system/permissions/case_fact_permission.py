"""
Case Fact Permission

Users can submit/update facts for their own cases.
Reviewers/Staff/Superadmin can view facts for cases they have access to.
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class CaseFactPermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Case Fact Permissions
    
    Users can submit/update facts for their own cases.
    Reviewers/Staff/Superadmin can view facts for cases they have access to.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        return RoleChecker.is_user(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership."""
        user = request.user
        
        # Get case from fact
        case = obj.case if hasattr(obj, 'case') else None
        if not case:
            return False
        
        # Superadmin/Staff can access all case facts
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can view case facts for assigned cases
        if RoleChecker.is_reviewer(user) and request.method in SAFE_METHODS:
            if self.is_reviewer_assigned_to_case(user, case):
                return True
            return True  # Reviewers can view all case facts (read-only)
        
        # User can manage facts for own cases
        if self.has_case_access(user, case):
            return True
        
        return False
