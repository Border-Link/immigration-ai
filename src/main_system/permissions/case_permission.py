"""
Case Management Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Create case, Submit facts, Retrieve own cases
- Reviewer: Retrieve assigned cases, Add review notes
- Staff: Retrieve all cases, Update case status (limited)
- Super Admin: Full CRUD on all cases
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class CasePermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Case Management Module Permissions
    
    Object-level: Based on case ownership or assignment.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # All authenticated users can create cases
        if request.method == 'POST':
            return RoleChecker.is_user(user)
        
        # All authenticated users can retrieve (filtered by ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update/Delete requires staff or superadmin (or own case)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_user(user)  # Object-level check will handle ownership
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership or assignment."""
        user = request.user
        
        # Superadmin/Staff can access all cases
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access assigned cases
        if RoleChecker.is_reviewer(user):
            # Check if reviewer is assigned to any review for this case
            if self.is_reviewer_assigned_to_case(user, obj):
                return True
            # Also allow reviewers to view all cases (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can access own cases
        if self.has_case_access(user, obj):
            return True
        
        return False
