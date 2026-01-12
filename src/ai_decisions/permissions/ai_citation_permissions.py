"""
Permission classes for AI Citation access control.

These permissions are specific to the ai_decisions module and provide
clear, self-documenting access control for AI citations.
"""
from rest_framework import permissions
from main_system.permissions.is_reviewer import IsReviewer
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff


class CanViewAICitation(permissions.BasePermission):
    """
    Permission to view AI citations.
    
    Rules:
    - User is reviewer (role='reviewer' AND is_staff/is_superuser)
    - User is admin/staff (is_staff OR is_superuser)
    
    AI citations are used for auditing and quality assurance, showing which
    sources the AI used in its reasoning. Restricted to reviewers and admins.
    
    Usage:
        permission_classes = [CanViewAICitation]
    """
    
    def has_permission(self, request, view):
        """Check if user is reviewer or admin/staff."""
        is_reviewer = IsReviewer()
        if is_reviewer.has_permission(request, view):
            return True
        
        is_admin_or_staff = IsAdminOrStaff()
        if is_admin_or_staff.has_permission(request, view):
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to view the AI citation.
        
        For now, if user has permission at the view level, they can view any citation.
        This could be extended to check case ownership if needed.
        """
        return self.has_permission(request, view)
