from rest_framework import permissions
from main_system.permissions.is_reviewer import IsReviewer
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff


class IsReviewerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow reviewers OR admin/staff users.
    
    This combines IsReviewer OR IsAdminOrStaff permissions.
    """
    
    def has_permission(self, request, view):
        # Check if user is reviewer
        is_reviewer = IsReviewer()
        if is_reviewer.has_permission(request, view):
            return True
        
        # Check if user is admin/staff
        is_admin_or_staff = IsAdminOrStaff()
        if is_admin_or_staff.has_permission(request, view):
            return True
        
        return False
