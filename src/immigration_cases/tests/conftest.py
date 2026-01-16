"""
Pytest configuration and shared fixtures for immigration_cases tests.

Key constraints:
- Do not call Django models directly in tests; use services as the entrypoint.
- Keep side-effects (email tasks, notifications, metrics, audit logging) isolated via mocks.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Tuple
from unittest.mock import MagicMock
import pytest
from rest_framework.test import APIClient
from users_access.services import UserService
from immigration_cases.services import CaseService, CaseFactService, CaseStatusHistoryService
from payments.services import PaymentService


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user_service():
    return UserService


@pytest.fixture
def case_service():
    return CaseService


@pytest.fixture
def case_fact_service():
    return CaseFactService


@pytest.fixture
def case_status_history_service():
    return CaseStatusHistoryService


@pytest.fixture
def payment_service():
    return PaymentService


@pytest.fixture
def case_owner(user_service):
    user = user_service.create_user(email="case-owner@example.com", password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def other_user(user_service):
    user = user_service.create_user(email="other-user@example.com", password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def admin_user(user_service):
    # is_staff=True is sufficient for AdminPermission / RoleChecker.is_staff
    user = user_service.create_user(email="admin-imm-cases@example.com", password="adminpass123")
    user_service.update_user(user, role="admin", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def reviewer_user(user_service):
    user = user_service.create_user(email="reviewer-imm-cases@example.com", password="reviewerpass123")
    user_service.update_user(user, role="reviewer", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def draft_case(case_service, case_owner):
    # Payment is required BEFORE case creation.
    pre_payment = PaymentService.create_payment(
        user_id=str(case_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_pre_case_001",
        plan="basic",
        changed_by=case_owner,
    )
    assert pre_payment is not None
    PaymentService.update_payment(
        payment_id=str(pre_payment.id),
        status="processing",
        changed_by=case_owner,
        reason="test payment processing",
    )
    PaymentService.update_payment(
        payment_id=str(pre_payment.id),
        status="completed",
        changed_by=case_owner,
        reason="test payment completion",
    )
    return case_service.create_case(
        user_id=str(case_owner.id),
        jurisdiction="US",
        status="draft",
    )


@pytest.fixture
def paid_case(case_service, payment_service, case_owner) -> Tuple[object, object]:
    """
    Returns: (case, payment)

    Payment is created (pre-case) and completed, then attached to the case during case creation.
    """
    payment = payment_service.create_payment(
        user_id=str(case_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_test_001",
        plan="basic",
        changed_by=case_owner,
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="processing",
        changed_by=case_owner,
        reason="test payment processing",
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="completed",
        changed_by=case_owner,
        reason="test payment completion",
    )
    assert payment is not None
    case = case_service.create_case(
        user_id=str(case_owner.id),
        jurisdiction="US",
        status="draft",
    )
    assert case is not None

    # Payment should now be attached to the case
    payment = payment_service.get_by_id(str(payment.id))
    assert payment is not None
    assert str(payment.case_id) == str(case.id)
    return case, payment


@pytest.fixture
def case_without_completed_payment(paid_case, payment_service, case_owner):
    """
    Create a valid case (requires prepayment) then soft-delete the attached payment,
    so downstream operations are blocked by payment validation.
    """
    case, payment = paid_case
    payment_service.delete_payment(
        payment_id=str(payment.id),
        changed_by=case_owner,
        reason="test delete payment",
        hard_delete=False,
    )
    from payments.helpers.payment_validator import PaymentValidator

    PaymentValidator.invalidate_payment_cache(str(case.id))
    return case


@pytest.fixture
def paid_case_with_fact(case_fact_service, paid_case):
    case, _payment = paid_case
    fact = case_fact_service.create_case_fact(
        case_id=str(case.id),
        fact_key="age",
        fact_value=30,
        source="user",
    )
    assert fact is not None
    return case, fact


@pytest.fixture(autouse=True)
def _isolate_side_effects(monkeypatch):
    """
    Isolate side-effects globally:
    - Notifications and email tasks emitted by signals
    - Metrics tracking and audit logging
    """
    # Signals side-effects
    from users_access.services import notification_service as notification_service_module
    from users_access.tasks import email_tasks as email_tasks_module

    create_notification_mock = MagicMock(name="create_notification")
    monkeypatch.setattr(notification_service_module.NotificationService, "create_notification", create_notification_mock)

    send_email_delay_mock = MagicMock(name="send_case_status_update_email_task.delay")
    monkeypatch.setattr(email_tasks_module.send_case_status_update_email_task, "delay", send_email_delay_mock)

    # Payments side-effects (Celery tasks + notifications)
    # PaymentNotificationService triggers a Celery task; keep tests deterministic and avoid Celery backend recursion.
    try:
        from payments.tasks import payment_tasks as payment_tasks_module

        monkeypatch.setattr(
            payment_tasks_module.send_payment_notification_task,
            "delay",
            MagicMock(name="send_payment_notification_task.delay"),
        )
    except Exception:
        # If payments.tasks isn't available in this test environment, ignore.
        pass

    # Metrics / audit (keep tests deterministic and fast)
    from immigration_cases.helpers import metrics as imm_metrics
    monkeypatch.setattr(imm_metrics, "track_case_creation", MagicMock(name="track_case_creation"))
    monkeypatch.setattr(imm_metrics, "track_case_update", MagicMock(name="track_case_update"))
    monkeypatch.setattr(imm_metrics, "track_case_status_transition", MagicMock(name="track_case_status_transition"))
    monkeypatch.setattr(imm_metrics, "track_case_version_conflict", MagicMock(name="track_case_version_conflict"))

    # Some modules call `track_case_status_history` but it may not exist in metrics (defensive)
    if hasattr(imm_metrics, "track_case_status_history"):
        monkeypatch.setattr(imm_metrics, "track_case_status_history", MagicMock(name="track_case_status_history"))

    from compliance.services import audit_log_service as audit_log_service_module
    monkeypatch.setattr(audit_log_service_module.AuditLogService, "create_audit_log", MagicMock(name="create_audit_log"))

    return {
        "create_notification_mock": create_notification_mock,
        "send_email_delay_mock": send_email_delay_mock,
    }

