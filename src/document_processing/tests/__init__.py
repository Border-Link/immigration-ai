"""
document_processing tests package.

Constraints:
- Do not call Django models directly in tests; use services as the entrypoint.
- Keep side-effects (Celery tasks, notifications, metrics, audit logging) isolated via mocks.
"""

