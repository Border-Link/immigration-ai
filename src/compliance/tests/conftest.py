"""
Pytest configuration and shared fixtures for compliance tests.

Production standard:
- Prefer services over direct model usage in tests.
"""

import pytest
from rest_framework.test import APIClient

from users_access.services.user_service import UserService
from compliance.services.audit_log_service import AuditLogService
from compliance.services.security_event_logger import SecurityEventLogger


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_service():
    return UserService


@pytest.fixture
def audit_log_service():
    return AuditLogService


@pytest.fixture
def security_event_logger():
    return SecurityEventLogger


@pytest.fixture
def admin_user(user_service):
    """
    Staff user with admin access (AdminPermission requires staff).
    """
    return user_service.create_superuser(email="admin@example.com", password="adminpass123")


@pytest.fixture
def staff_user(user_service):
    """
    Staff (non-superuser) user with admin access.
    """
    user = user_service.create_user(email="staff@example.com", password="staffpass123")
    user_service.update_user(user, is_staff=True, role="reviewer")
    user_service.activate_user(user)
    return user


@pytest.fixture
def normal_user(user_service):
    """
    Authenticated user without staff privileges (should be forbidden for admin endpoints).
    """
    user = user_service.create_user(email="user@example.com", password="userpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def make_audit_log(audit_log_service):
    """
    Factory fixture for creating audit logs via the service layer.
    """

    def _make(**kwargs):
        defaults = {
            "level": "INFO",
            "logger_name": "tests.compliance",
            "message": "test message",
            "pathname": "/tmp/test.py",
            "lineno": 123,
            "func_name": "test_func",
            "process": 999,
            "thread": "MainThread",
        }
        defaults.update(kwargs)
        return audit_log_service.create_audit_log(**defaults)

    return _make

