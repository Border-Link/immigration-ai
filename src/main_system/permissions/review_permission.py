"""
Review Service Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Request review (manual escalation)
- Reviewer: Access assigned review tasks, Approve/reject/override, Add notes
- Staff: Monitor reviews
- Super Admin: Full review management, reassign reviewers, audit reviews
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class ReviewPermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Review Service Module Permissions
    
    Object-level: Based on review assignment or case ownership.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # All authenticated users can request reviews
        if request.method == 'POST':
            return RoleChecker.is_user(user)
        
        # All authenticated users can view (filtered by assignment/ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update/Delete requires reviewer, staff, or superadmin
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_reviewer(user)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on review assignment or case ownership."""
        user = request.user
        
        # Superadmin/Staff can access all reviews
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access assigned reviews
        if RoleChecker.is_reviewer(user):
            if hasattr(obj, 'reviewer') and obj.reviewer == user:
                return True
            # Reviewers can also view all reviews (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can access reviews for own cases
        if hasattr(obj, 'case') and self.has_case_access(user, obj.case):
            return True
        
        return False
