"""
Payment Module Permission

Users can view and create payments for their own cases.
Staff/Superadmin can view all payments.
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class PaymentPermission(BaseModulePermission, CaseOwnershipMixin):
    """
    Payment Module Permissions
    
    Object-level: Based on case ownership.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # All authenticated users can create payments
        if request.method == 'POST':
            return RoleChecker.is_user(user)
        
        # All authenticated users can view (filtered by case ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Update/Delete requires staff or superadmin (or own case)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_user(user)  # Object-level check will handle ownership
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership."""
        user = request.user
        
        # Superadmin/Staff can access all payments
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True

        # Get case from payment (case-attached payments)
        case = obj.case if hasattr(obj, 'case') else None
        if case:
            # User can access payments for own cases
            return self.has_case_access(user, case)

        # Pre-case payments: allow access to the owning user
        payment_user = getattr(obj, "user", None)
        if payment_user and getattr(payment_user, "id", None) == getattr(user, "id", None):
            return True
        
        return False
