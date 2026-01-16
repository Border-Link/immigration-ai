"""
Pytest configuration and shared fixtures for ai_calls tests.

Key constraints (mirrors users_access / immigration_cases):
- Do not call Django models directly in tests; use services as the entrypoint.
- Isolate side-effects (Celery, notifications, metrics, audit logging) via mocks.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Any, Tuple
from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIClient

from users_access.services import UserService
from payments.services import PaymentService
from payments.services.pricing_service import PricingService
from immigration_cases.services import CaseService

from ai_calls.services.call_session_service import CallSessionService
from ai_calls.services.voice_orchestrator import VoiceOrchestrator


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user_service():
    return UserService


@pytest.fixture
def payment_service():
    return PaymentService


@pytest.fixture
def pricing_service():
    return PricingService


@pytest.fixture
def case_service():
    return CaseService


@pytest.fixture
def call_session_service():
    return CallSessionService


@pytest.fixture
def voice_orchestrator():
    return VoiceOrchestrator


@pytest.fixture
def case_owner(user_service):
    user = user_service.create_user(email="ai-calls-owner@example.com", password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def other_user(user_service):
    user = user_service.create_user(email="ai-calls-other@example.com", password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def admin_user(user_service):
    # is_staff=True is sufficient for AdminPermission / RoleChecker.is_staff
    user = user_service.create_user(email="ai-calls-admin@example.com", password="adminpass123")
    user_service.update_user(user, role="admin", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def paid_case(case_service, payment_service, pricing_service, case_owner) -> Tuple[object, object]:
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
        provider_transaction_id="txn_ai_calls_case_001",
        plan="special",
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

    case = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
    assert case is not None

    # Configure plan entitlements for tests: "special" includes AI calls.
    # (Entitlements are DB-driven via PricingItem now.)
    item = pricing_service.create_item(
        kind="plan",
        code="special",
        name="Special Plan",
        description="",
        is_active=True,
        includes_ai_calls=True,
        includes_human_review=False,
    )
    assert item is not None

    return case, payment


@pytest.fixture
def minimal_context_bundle(paid_case) -> Dict[str, Any]:
    case, _payment = paid_case
    return {
        "case_id": str(case.id),
        "case_facts": {"jurisdiction": "US"},
        "documents_summary": {"uploaded": [], "missing": [], "status": {}},
        "restricted_topics": [],
    }


@pytest.fixture
def call_session_created(call_session_service, paid_case, case_owner):
    case, _payment = paid_case
    call_session = call_session_service.create_call_session(case_id=str(case.id), user_id=str(case_owner.id))
    assert call_session is not None
    return call_session


@pytest.fixture
def call_session_ready(monkeypatch, call_session_service, call_session_created, minimal_context_bundle):
    from ai_calls.services import case_context_builder as case_context_builder_module

    monkeypatch.setattr(
        case_context_builder_module.CaseContextBuilder,
        "build_context_bundle",
        MagicMock(name="build_context_bundle", return_value=minimal_context_bundle),
    )
    # Use real validation; the bundle includes required fields.
    prepared = call_session_service.prepare_call_session(str(call_session_created.id))
    assert prepared is not None
    assert prepared.status == "ready"
    return prepared


@pytest.fixture
def call_session_in_progress(monkeypatch, call_session_service, call_session_ready):
    from ai_calls.services import timebox_service as timebox_service_module

    monkeypatch.setattr(
        timebox_service_module.TimeboxService,
        "schedule_timebox_enforcement",
        MagicMock(name="schedule_timebox_enforcement", return_value="task_ai_calls_001"),
    )

    started = call_session_service.start_call(str(call_session_ready.id))
    assert started is not None
    assert started.status == "in_progress"
    return started


@pytest.fixture(autouse=True)
def _isolate_side_effects(monkeypatch):
    """
    Isolate side-effects globally:
    - Notifications and email tasks emitted by signals
    - Payments notifications (Celery)
    - Metrics tracking and audit logging
    - Celery revoke calls (timebox cancellation)
    """
    # Users notifications / emails
    from users_access.services import notification_service as notification_service_module
    from users_access.tasks import email_tasks as email_tasks_module

    monkeypatch.setattr(
        notification_service_module.NotificationService,
        "create_notification",
        MagicMock(name="NotificationService.create_notification"),
    )
    monkeypatch.setattr(
        email_tasks_module.send_case_status_update_email_task,
        "delay",
        MagicMock(name="send_case_status_update_email_task.delay"),
    )

    # Payments notification task
    try:
        from payments.tasks import payment_tasks as payment_tasks_module

        monkeypatch.setattr(
            payment_tasks_module.send_payment_notification_task,
            "delay",
            MagicMock(name="send_payment_notification_task.delay"),
        )
    except Exception:
        pass

    # Metrics / audit logging
    try:
        from immigration_cases.helpers import metrics as imm_metrics

        for fn in [
            "track_case_creation",
            "track_case_update",
            "track_case_status_transition",
            "track_case_version_conflict",
            "track_case_status_history",
        ]:
            if hasattr(imm_metrics, fn):
                monkeypatch.setattr(imm_metrics, fn, MagicMock(name=f"imm_metrics.{fn}"))
    except Exception:
        pass

    try:
        from compliance.services import audit_log_service as audit_log_service_module

        monkeypatch.setattr(
            audit_log_service_module.AuditLogService,
            "create_audit_log",
            MagicMock(name="AuditLogService.create_audit_log"),
        )
    except Exception:
        pass

    # Celery revoke (TimeboxService.cancel_timebox_enforcement)
    try:
        import celery

        monkeypatch.setattr(
            celery.current_app.control,
            "revoke",
            MagicMock(name="celery.current_app.control.revoke"),
        )
    except Exception:
        pass

