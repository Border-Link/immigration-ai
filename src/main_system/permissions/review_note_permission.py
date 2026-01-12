"""
Review Note Permission

Reviewers can add notes to assigned reviews.
Users can view notes for their own case reviews.
Staff/Superadmin can view all notes.
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class ReviewNotePermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Review Note Permissions
    
    Reviewers can add notes to assigned reviews.
    Users can view notes for their own case reviews.
    Staff/Superadmin can view all notes.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # Reviewers, staff, and superadmin can create notes
        if request.method == 'POST':
            return RoleChecker.is_reviewer(user)
        
        # All authenticated users can view (filtered by review access)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update/Delete requires reviewer, staff, or superadmin
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_reviewer(user)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on review assignment."""
        user = request.user
        
        # Get review from note
        review = obj.review if hasattr(obj, 'review') else None
        if not review:
            return False
        
        # Superadmin/Staff can access all review notes
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access notes for assigned reviews
        if RoleChecker.is_reviewer(user):
            if hasattr(review, 'reviewer') and review.reviewer == user:
                return True
            # Reviewers can view all notes (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can view notes for own case reviews
        if hasattr(review, 'case') and self.has_case_access(user, review.case):
            return True
        
        return False
