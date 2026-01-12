from rest_framework import permissions


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
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser always has reviewer access
        if request.user.is_superuser:
            return True
        
        # Staff flag grants reviewer access
        if request.user.is_staff:
            return True
        
        # Admin role grants reviewer access
        if request.user.role == 'admin':
            return True
        
        # Reviewer role with staff/superuser flag
        if request.user.role == 'reviewer' and (request.user.is_staff or request.user.is_superuser):
            return True
        
        return False

