# Read views
from .read import (
    StateProvinceListAPI,
    StateProvinceDetailAPI,
    StateProvinceNominationProgramsAPI
)

# Create views
from .create import (
    StateProvinceCreateAPI
)

# Update/Delete views
from .update_delete import (
    StateProvinceUpdateAPI,
    StateProvinceDeleteAPI
)

__all__ = [
    # Read
    'StateProvinceListAPI',
    'StateProvinceDetailAPI',
    'StateProvinceNominationProgramsAPI',
    # Create
    'StateProvinceCreateAPI',
    # Update/Delete
    'StateProvinceUpdateAPI',
    'StateProvinceDeleteAPI',
]

