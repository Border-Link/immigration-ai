"""
Document Service Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Upload documents, View own documents
- Reviewer: Access documents for assigned cases, Validate document classification
- Staff: Access all documents, Delete/reclassify documents
- Super Admin: Full access to all documents and storage settings
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class DocumentPermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Document Service Module Permissions
    
    Object-level: Based on case ownership or assignment.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # All authenticated users can upload documents
        if request.method == 'POST':
            return RoleChecker.is_user(user)
        
        # All authenticated users can view (filtered by ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update/Delete requires staff or superadmin (or own case)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_user(user)  # Object-level check will handle ownership
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership or assignment."""
        user = request.user
        
        # Get case from document
        case = obj.case if hasattr(obj, 'case') else None
        if not case:
            return False
        
        # Superadmin/Staff can access all documents
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access documents for assigned cases
        if RoleChecker.is_reviewer(user):
            if self.is_reviewer_assigned_to_case(user, case):
                return True
            # Reviewers can view all documents (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can access documents for own cases
        if self.has_case_access(user, case):
            return True
        
        return False
