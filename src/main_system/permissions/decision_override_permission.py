"""
Decision Override Permission

Reviewers can create overrides for assigned reviews.
Users can view overrides for their own cases.
Staff/Superadmin can view all overrides.
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class DecisionOverridePermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Decision Override Permissions
    
    Reviewers can create overrides for assigned reviews.
    Users can view overrides for their own cases.
    Staff/Superadmin can view all overrides.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # Reviewers, staff, and superadmin can create overrides
        if request.method == 'POST':
            return RoleChecker.is_reviewer(user)
        
        # All authenticated users can view (filtered by case ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update/Delete requires staff or superadmin
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_staff(user)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership or assignment."""
        user = request.user
        
        # Get case from override
        case = obj.case if hasattr(obj, 'case') else None
        if not case:
            return False
        
        # Superadmin/Staff can access all overrides
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access overrides for assigned cases
        if RoleChecker.is_reviewer(user):
            if self.is_reviewer_assigned_to_case(user, case):
                return True
            # Reviewers can view all overrides (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can view overrides for own cases
        if self.has_case_access(user, case):
            return True
        
        return False
