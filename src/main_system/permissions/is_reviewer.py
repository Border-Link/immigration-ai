from rest_framework import permissions
from main_system.permissions.role_checker import RoleChecker


class IsReviewer(permissions.BasePermission):
    """
    Custom permission to allow reviewers, staff, and superadmin users.
    
    According to ROLE_TO_IMPLEMENT.md:
    - Reviewer: role in ['reviewer', 'staff', 'superadmin']
    
    Implementation:
    - role='reviewer' OR is_staff=True OR is_superuser=True OR role='admin'
    (since reviewers need staff/superuser flags, and admin role also grants reviewer access)
    """

    def has_permission(self, request, view):
        """Check if user is reviewer, staff, or superuser."""
        user = getattr(request, 'user', None)
        return RoleChecker.is_reviewer(user)

