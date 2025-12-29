from .is_superuser import IsSuperUser
from .is_admin_or_staff import IsAdminOrStaff
from .is_reviewer import IsReviewer
from .factories.has_permission import HasPermission

__all__ = [
    'IsSuperUser',
    'IsAdminOrStaff',
    'IsReviewer',
    'HasPermission',
]

