from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    """
    Custom permission to allow staff and superadmin users.
    
    According to ROLE_TO_IMPLEMENT.md:
    - Staff: role in ['staff', 'superadmin']
    
    Implementation:
    - is_staff=True OR is_superuser=True OR role='admin'
    (since the User model uses role='admin' for admin users and is_staff/is_superuser flags)
    """
    
    def has_permission(self, request, view):
        """Check if user is staff or superuser."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser always has staff access
        if request.user.is_superuser:
            return True
        
        # Staff flag grants access
        if request.user.is_staff:
            return True
        
        # Admin role grants staff access
        if request.user.role == 'admin':
            return True
        
        return False
