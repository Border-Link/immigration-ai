from .case.create import CaseCreateAPI
from .case.read import CaseListAPI, CaseDetailAPI
from .case.update_delete import CaseUpdateAPI, CaseDeleteAPI
from .case.eligibility import CaseEligibilityCheckAPI, CaseEligibilityExplanationAPI
from .case_fact.create import CaseFactCreateAPI
from .case_fact.read import CaseFactListAPI, CaseFactDetailAPI
from .case_fact.update_delete import CaseFactUpdateAPI, CaseFactDeleteAPI

# Admin views
from .admin.case_admin import (
    CaseAdminListAPI,
    CaseAdminDetailAPI,
    CaseAdminUpdateAPI,
    CaseAdminDeleteAPI,
    BulkCaseOperationAPI,
)
from .admin.case_fact_admin import (
    CaseFactAdminListAPI,
    CaseFactAdminDetailAPI,
    CaseFactAdminUpdateAPI,
    CaseFactAdminDeleteAPI,
    BulkCaseFactOperationAPI,
)
from .admin.immigration_cases_analytics import ImmigrationCasesStatisticsAPI

__all__ = [
    'CaseCreateAPI',
    'CaseListAPI',
    'CaseDetailAPI',
    'CaseUpdateAPI',
    'CaseDeleteAPI',
    'CaseEligibilityCheckAPI',
    'CaseEligibilityExplanationAPI',
    'CaseFactCreateAPI',
    'CaseFactListAPI',
    'CaseFactDetailAPI',
    'CaseFactUpdateAPI',
    'CaseFactDeleteAPI',
    # Admin
    'CaseAdminListAPI',
    'CaseAdminDetailAPI',
    'CaseAdminUpdateAPI',
    'CaseAdminDeleteAPI',
    'BulkCaseOperationAPI',
    'CaseFactAdminListAPI',
    'CaseFactAdminDetailAPI',
    'CaseFactAdminUpdateAPI',
    'CaseFactAdminDeleteAPI',
    'BulkCaseFactOperationAPI',
    'ImmigrationCasesStatisticsAPI',
]

