"""
Pytest configuration and shared fixtures for payments tests.

Mirrors `users_access/tests` and `immigration_cases/tests` conventions:
- Services are the entrypoints (no direct model creation in tests).
- Side-effects (Celery/email/notifications/metrics/audit) are mocked for determinism.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIClient

from users_access.services import UserService
from immigration_cases.services import CaseService
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
def payment_service():
    return PaymentService


@pytest.fixture
def payment_owner(user_service):
    user = user_service.create_user(email="payment-owner@example.com", password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def other_user(user_service):
    user = user_service.create_user(email="payment-other@example.com", password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def admin_user(user_service):
    user = user_service.create_user(email="payment-admin@example.com", password="adminpass123")
    user_service.update_user(user, role="admin", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def pre_case_payment_pending(payment_service, payment_owner):
    return payment_service.create_payment(
        user_id=str(payment_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id=None,
        plan="basic",
        changed_by=payment_owner,
    )


@pytest.fixture
def pre_case_payment_with_txn_pending(payment_service, payment_owner):
    return payment_service.create_payment(
        user_id=str(payment_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_pre_case_001",
        plan="basic",
        changed_by=payment_owner,
    )


@pytest.fixture
def pre_case_payment_completed(payment_service, payment_owner):
    payment = payment_service.create_payment(
        user_id=str(payment_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_completed_001",
        plan="basic",
        changed_by=payment_owner,
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="processing",
        changed_by=payment_owner,
        reason="processing for test",
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="completed",
        changed_by=payment_owner,
        reason="completed for test",
    )
    assert payment is not None
    return payment


@pytest.fixture
def pre_case_payment_failed(payment_service, payment_owner):
    payment = payment_service.create_payment(
        user_id=str(payment_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_failed_001",
        plan="basic",
        changed_by=payment_owner,
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="failed",
        changed_by=payment_owner,
        reason="failed for test",
    )
    assert payment is not None
    return payment


@pytest.fixture
def paid_case(case_service, payment_service, payment_owner):
    """
    Returns (case, attached_payment).

    Payment is created pre-case, completed, then attached during case creation.
    """
    pre_payment = payment_service.create_payment(
        user_id=str(payment_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_case_attach_001",
        plan="basic",
        changed_by=payment_owner,
    )
    assert pre_payment is not None
    payment_service.update_payment(payment_id=str(pre_payment.id), status="processing", changed_by=payment_owner, reason="processing")
    payment_service.update_payment(payment_id=str(pre_payment.id), status="completed", changed_by=payment_owner, reason="completed")

    case = case_service.create_case(user_id=str(payment_owner.id), jurisdiction="US", status="draft")
    assert case is not None

    attached = payment_service.get_by_id(str(pre_payment.id))
    assert attached is not None
    assert str(attached.case_id) == str(case.id)
    return case, attached


@pytest.fixture
def case_without_completed_payment(paid_case, payment_service, payment_owner):
    """
    Create a valid case (requires prepayment) then soft-delete the attached payment,
    so downstream operations are blocked by payment validation.
    """
    case, payment = paid_case
    payment_service.delete_payment(
        payment_id=str(payment.id),
        changed_by=payment_owner,
        reason="test delete payment",
        hard_delete=False,
    )
    from payments.helpers.payment_validator import PaymentValidator

    PaymentValidator.invalidate_payment_cache(str(case.id))
    return case


@pytest.fixture(autouse=True)
def _isolate_side_effects(monkeypatch):
    """
    Keep tests deterministic:
    - Disable notifications
    - Disable celery .delay fanout
    - Disable audit logging + prometheus metrics
    """
    # In-app notifications
    from users_access.services import notification_service as notification_service_module

    monkeypatch.setattr(
        notification_service_module.NotificationService,
        "create_notification",
        MagicMock(name="NotificationService.create_notification"),
    )

    # Payments celery tasks
    from payments.tasks import payment_tasks as payment_tasks_module

    monkeypatch.setattr(
        payment_tasks_module.send_payment_notification_task,
        "delay",
        MagicMock(name="send_payment_notification_task.delay"),
    )

    # Audit logging
    from compliance.services import audit_log_service as audit_log_service_module

    monkeypatch.setattr(
        audit_log_service_module.AuditLogService,
        "create_audit_log",
        MagicMock(name="AuditLogService.create_audit_log"),
    )

    # Metrics
    from payments.helpers import metrics as payment_metrics

    monkeypatch.setattr(payment_metrics, "track_payment_creation", MagicMock(name="track_payment_creation"))
    monkeypatch.setattr(payment_metrics, "track_payment_status_transition", MagicMock(name="track_payment_status_transition"))
    monkeypatch.setattr(payment_metrics, "track_payment_revenue", MagicMock(name="track_payment_revenue"))
    monkeypatch.setattr(payment_metrics, "update_payments_by_status", MagicMock(name="update_payments_by_status"))

    return True

