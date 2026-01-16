"""
Import-sanity tests to ensure ai_decisions modules load in production settings.

This catches broken imports in package wiring (apps/admin/urls/views exports).
"""


def test_ai_decisions_module_imports():
    import ai_decisions  # noqa: F401
    import ai_decisions.apps  # noqa: F401
    import ai_decisions.admin  # noqa: F401
    import ai_decisions.urls  # noqa: F401
    import ai_decisions.views  # noqa: F401

