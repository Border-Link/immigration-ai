"""
Rule Engine Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Run eligibility checks (read-only, cannot modify rules)
- Reviewer: Read-only (see rule outcomes)
- Staff: Create/edit rules (limited to staging, maybe)
- Super Admin: Full rule management (publish, archive, override)
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .role_checker import RoleChecker


class RulePermission(BaseModulePermission):
    """
    Rule Engine Module Permissions
    
    Note: Users can run eligibility checks (which uses rules) but cannot modify rules.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # Read operations: All authenticated users can view rules (for eligibility checks)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Write operations: Staff and Superadmin only
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_staff(user)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Same as module-level."""
        return self.has_permission(request, view)
