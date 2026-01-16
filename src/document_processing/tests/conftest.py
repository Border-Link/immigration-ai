"""
Shared fixtures for document_processing tests.

Production testing standards:
- Prefer creating state through services (not direct models).
- Explicitly cover payment-gated flows: paid case vs blocked case.
- Isolate side effects: Celery, notifications, email tasks, audit logging, metrics.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Tuple
from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIClient

from users_access.services import UserService
from immigration_cases.services import CaseService
from payments.services import PaymentService
from rules_knowledge.services.document_type_service import DocumentTypeService
from document_handling.services.case_document_service import CaseDocumentService

from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.services.processing_history_service import ProcessingHistoryService


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
def document_type_service():
    return DocumentTypeService


@pytest.fixture
def case_document_service():
    return CaseDocumentService


@pytest.fixture
def processing_job_service():
    return ProcessingJobService


@pytest.fixture
def processing_history_service():
    return ProcessingHistoryService


@pytest.fixture
def case_owner(user_service):
    user = user_service.create_user(email="dp-owner@example.com", password="OwnerPass123!@#")
    assert user is not None
    # Many services gate behavior on verification; keep it consistent with production.
    try:
        user_service.activate_user(user)
    except Exception:
        # If activate_user isn't required in this codepath, ignore.
        pass
    return user


@pytest.fixture
def admin_user(user_service):
    user = user_service.create_superuser(email="dp-admin@example.com", password="AdminPass123!@#")
    assert user is not None
    return user


@pytest.fixture
def paid_case(case_service, payment_service, case_owner) -> Tuple[object, object]:
    """
    Returns: (case, payment)

    Payment is created (pre-case) and completed, then attached to the case during case creation.
    Mirrors production flow (see immigration_cases/tests/conftest.py).
    """
    payment = payment_service.create_payment(
        user_id=str(case_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id="txn_dp_test_001",
        plan="basic",
        changed_by=case_owner,
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="processing",
        changed_by=case_owner,
        reason="dp test payment processing",
    )
    assert payment is not None
    payment = payment_service.update_payment(
        payment_id=str(payment.id),
        status="completed",
        changed_by=case_owner,
        reason="dp test payment completion",
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
    deleted = payment_service.delete_payment(
        payment_id=str(payment.id),
        changed_by=case_owner,
        reason="dp test delete payment",
        hard_delete=False,
    )
    assert deleted is True
    from payments.helpers.payment_validator import PaymentValidator

    PaymentValidator.invalidate_payment_cache(str(case.id))
    return case


@pytest.fixture
def active_document_type(document_type_service, monkeypatch):
    # Audit logging is orthogonal to document_processing tests; isolate it.
    try:
        from compliance.services import audit_log_service as audit_log_service_module

        monkeypatch.setattr(
            audit_log_service_module.AuditLogService,
            "create_audit_log",
            MagicMock(name="AuditLogService.create_audit_log"),
            raising=True,
        )
    except Exception:
        pass

    doc_type = document_type_service.create_document_type(
        code="DP_TEST_DOC",
        name="DP Test Document",
        description="Document type for document_processing tests",
        is_active=True,
    )
    assert doc_type is not None
    return doc_type


@pytest.fixture
def case_document(case_document_service, paid_case, active_document_type):
    case, _payment = paid_case
    doc = case_document_service.create_case_document(
        case_id=str(case.id),
        document_type_id=str(active_document_type.id),
        file_path="case_documents/dp_tests/test.pdf",
        file_name="dp_test.pdf",
        file_size=2048,
        mime_type="application/pdf",
        status="uploaded",
    )
    assert doc is not None
    return doc


@pytest.fixture(autouse=True)
def _isolate_side_effects(monkeypatch):
    """
    Globally isolate side-effects to keep tests deterministic and scalable:
    - Celery tasks triggered by document_handling signals
    - Notifications/email tasks
    - Payment notifications tasks
    """
    # document_handling post_save signals call process_document_task.delay()
    try:
        from document_handling.tasks import document_tasks as document_tasks_module

        monkeypatch.setattr(
            document_tasks_module.process_document_task,
            "delay",
            MagicMock(name="process_document_task.delay"),
            raising=False,
        )
    except Exception:
        pass

    # Notification side effects
    try:
        from users_access.services import notification_service as notification_service_module

        monkeypatch.setattr(
            notification_service_module.NotificationService,
            "create_notification",
            MagicMock(name="NotificationService.create_notification"),
            raising=True,
        )
    except Exception:
        pass

    # Email tasks invoked by document signals
    try:
        from users_access.tasks import email_tasks as email_tasks_module

        monkeypatch.setattr(
            email_tasks_module.send_document_status_email_task,
            "delay",
            MagicMock(name="send_document_status_email_task.delay"),
            raising=False,
        )
    except Exception:
        pass

    # Payment notification tasks
    try:
        from payments.tasks import payment_tasks as payment_tasks_module

        monkeypatch.setattr(
            payment_tasks_module.send_payment_notification_task,
            "delay",
            MagicMock(name="send_payment_notification_task.delay"),
            raising=False,
        )
    except Exception:
        pass

