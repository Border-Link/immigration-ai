"""
Import-sanity tests to ensure ai_calls modules load in production settings.

This helps catch broken imports and also ensures basic coverage across
non-service modules (apps/admin/urls/views exports).
"""


def test_ai_calls_module_imports():
    import ai_calls  # noqa: F401
    import ai_calls.apps  # noqa: F401
    import ai_calls.admin  # noqa: F401
    import ai_calls.urls  # noqa: F401
    import ai_calls.views  # noqa: F401

