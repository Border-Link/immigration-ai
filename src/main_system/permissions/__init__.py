# Role-based permissions (from ROLE_TO_IMPLEMENT.md)
from .is_user import IsUser
from .is_reviewer import IsReviewer
from .is_staff import IsStaff
from .is_superadmin import IsSuperAdmin

# Legacy permissions (kept for backward compatibility)
from .is_superuser import IsSuperUser
from .is_admin_or_staff import IsAdminOrStaff
from .is_reviewer_or_admin import IsReviewerOrAdmin

# Case ownership helpers
from .case_ownership import CaseOwnershipPermission
from .has_case_ownership import HasCaseOwnership, HasCaseWriteAccess

# Base permissions and utilities
from .base_permissions import BaseModulePermission
from .role_checker import RoleChecker
from .case_ownership_mixin import CaseOwnershipMixin

# Module-specific permissions (one class per file)
from .authentication_permission import AuthenticationPermission
from .case_permission import CasePermission
from .case_fact_permission import CaseFactPermission
from .rule_permission import RulePermission
from .document_permission import DocumentPermission
from .ai_reasoning_permission import AIReasoningPermission
from .ingestion_permission import IngestionPermission
from .review_permission import ReviewPermission
from .review_note_permission import ReviewNotePermission
from .decision_override_permission import DecisionOverridePermission
from .admin_permission import AdminPermission
from .payment_permission import PaymentPermission
from .rule_validation_task_permission import RuleValidationTaskPermission

__all__ = [
    # Role-based permissions (from ROLE_TO_IMPLEMENT.md)
    'IsUser',
    'IsReviewer',
    'IsStaff',
    'IsSuperAdmin',
    # Legacy permissions (kept for backward compatibility)
    'IsSuperUser',
    'IsAdminOrStaff',
    'IsReviewerOrAdmin',
    # Case ownership helpers
    'CaseOwnershipPermission',
    'HasCaseOwnership',
    'HasCaseWriteAccess',
    # Base permissions and utilities
    'BaseModulePermission',
    'RoleChecker',
    'CaseOwnershipMixin',
    # Module-specific permissions (one class per file)
    'AuthenticationPermission',
    'CasePermission',
    'CaseFactPermission',
    'RulePermission',
    'DocumentPermission',
    'AIReasoningPermission',
    'IngestionPermission',
    'ReviewPermission',
    'ReviewNotePermission',
    'DecisionOverridePermission',
    'AdminPermission',
    'PaymentPermission',
    'RuleValidationTaskPermission',
]

