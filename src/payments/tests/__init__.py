"""
Payments test package.

Constraints (enforced by convention in this suite):
- Do not create/query models directly in tests; use services as entrypoints.
- Isolate side-effects (Celery tasks, notifications, external HTTP) via mocks.
"""

