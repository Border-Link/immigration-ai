"""
AI Reasoning Service Module Permission

According to ROLE_TO_IMPLEMENT.md:
- User: Trigger AI reasoning for own cases (read-only results)
- Reviewer: Access AI outputs for assigned cases
- Staff: View AI logs, cannot edit
- Super Admin: Full access to AI logs, LLM prompts, embeddings
"""
from rest_framework.permissions import SAFE_METHODS
from .base_permissions import BaseModulePermission
from .case_ownership_mixin import CaseOwnershipMixin
from .role_checker import RoleChecker


class AIReasoningPermission(BaseModulePermission, CaseOwnershipMixin):
    """
    AI Reasoning Service Module Permissions
    
    Object-level: Access tied to case ownership/assignment.
    """
    
    def has_permission(self, request, view):
        """Module-level permission check."""
        user = request.user
        
        # All authenticated users can trigger AI reasoning (for their own cases)
        if request.method == 'POST':
            return RoleChecker.is_user(user)
        
        # All authenticated users can view (filtered by ownership)
        if request.method in SAFE_METHODS:
            return RoleChecker.is_user(user)
        
        # Write operations: All authenticated users (object-level check will handle ownership)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleChecker.is_user(user)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permission: Based on case ownership or assignment."""
        user = request.user
        
        # Get case from AI reasoning log/result
        case = None
        if hasattr(obj, 'case'):
            case = obj.case
        elif hasattr(obj, 'eligibility_result') and hasattr(obj.eligibility_result, 'case'):
            case = obj.eligibility_result.case
        
        if not case:
            return False
        
        # Superadmin/Staff can access all AI reasoning
        if RoleChecker.is_superadmin(user) or RoleChecker.is_staff(user):
            return True
        
        # Reviewer can access AI outputs for assigned cases
        if RoleChecker.is_reviewer(user):
            if self.is_reviewer_assigned_to_case(user, case):
                return True
            # Reviewers can view all AI reasoning logs (read-only)
            if request.method in SAFE_METHODS:
                return True
        
        # User can access AI reasoning for own cases
        if self.has_case_access(user, case):
            return True
        
        return False
