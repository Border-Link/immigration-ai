"""
AI Call Service Module Permission

According to MODULE_PERMISSIONS_GUIDE.md and ROLE_TO_IMPLEMENT.md:
- User: Create call session, View own call sessions, Initiate calls
- Reviewer: View call sessions for assigned cases
- Staff: View all call sessions, Monitor calls
- Super Admin: Full access to all call sessions and analytics
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class AiCallPermission(BaseModulePermission, CaseOwnershipMixin):
    """
    AI Call Service Module Permissions
    
    Object-level: Based on case ownership or assignment.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # All authenticated users can create call sessions
        if request.method == 'POST':
            return RoleChecker.is_user(user)
        
        # All authenticated users can retrieve (filtered by ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update operations (prepare, start, end, terminate) require ownership
        if request.method in ['PUT', 'PATCH']:
            return RoleChecker.is_user(user)  # Object-level check will handle ownership
        
        # Delete requires staff or superadmin
        if request.method == 'DELETE':
            return RoleChecker.is_staff(user) or RoleChecker.is_superadmin(user)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership or assignment."""
        user = request.user
        
        # Superadmin/Staff can access all call sessions
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access call sessions for assigned cases
        if RoleChecker.is_reviewer(user):
            # Check if reviewer is assigned to any review for this case
            if self.is_reviewer_assigned_to_case(user, obj.case):
                return True
            # Also allow reviewers to view all call sessions (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can access own call sessions (based on case ownership)
        if self.has_case_access(user, obj.case):
            return True
        
        return False
