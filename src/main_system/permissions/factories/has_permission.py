from rest_framework.permissions import BasePermission

class HasPermission(BasePermission):
    """
    Custom permission to check if the user has a specific permission.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if the user has the required permission
        required_perm = getattr(view, 'permission_required', None)
        if required_perm is None:
            raise AttributeError(
                "The view must have a 'permission_required' attribute set to the required permission."
            )
        return request.user.has_perm(required_perm)