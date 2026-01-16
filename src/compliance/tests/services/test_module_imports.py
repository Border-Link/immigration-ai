"""
Coverage-oriented import tests for small modules.

We keep these extremely lightweight and side-effect-safe.
"""

import pytest


@pytest.mark.django_db
def test_imports_smoke():
    import compliance.admin  # noqa: F401
    import compliance.apps  # noqa: F401
    import compliance.urls  # noqa: F401
    import compliance.views  # noqa: F401
    import compliance.views.audit_log.read  # noqa: F401
    import compliance.serializers.audit_log.read  # noqa: F401
    import compliance.signals  # noqa: F401

