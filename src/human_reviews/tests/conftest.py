"""
Pytest configuration and shared fixtures for human_reviews tests.

Conventions (aligned with users_access + immigration_cases + ai_decisions):
- Do not call Django models directly in tests; use services as the entrypoint.
- Keep side-effects (email tasks, notifications, metrics, audit logging) isolated via mocks.
- Clear shared cache between tests to avoid coupling due to @cache_result usage.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Tuple
from unittest.mock import MagicMock

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from main_system.utils.cache_utils import cache_clear
from users_access.services import UserService
from immigration_cases.services import CaseService
from payments.services import PaymentService
from rules_knowledge.services.visa_type_service import VisaTypeService
from rules_knowledge.services.visa_rule_version_service import VisaRuleVersionService
from ai_decisions.services.eligibility_result_service import EligibilityResultService

from human_reviews.services.review_service import ReviewService
from human_reviews.services.review_note_service import ReviewNoteService
from human_reviews.services.decision_override_service import DecisionOverrideService


@pytest.fixture(autouse=True)
def _clear_cache():
    """Avoid cross-test cache coupling due to @cache_result usage."""
    cache_clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# -----------------------------------------------------------------------------
# Service fixtures (return the class, same pattern as users_access)
# -----------------------------------------------------------------------------

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
def visa_type_service():
    return VisaTypeService


@pytest.fixture
def visa_rule_version_service():
    return VisaRuleVersionService


@pytest.fixture
def eligibility_result_service():
    return EligibilityResultService


@pytest.fixture
def review_service():
    return ReviewService


@pytest.fixture
def review_note_service():
    return ReviewNoteService


@pytest.fixture
def decision_override_service():
    return DecisionOverrideService


# -----------------------------------------------------------------------------
# User fixtures (roles align with RoleChecker/AdminPermission)
# -----------------------------------------------------------------------------

@pytest.fixture
def case_owner(user_service):
    email = f"case-owner-human-reviews-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def other_user(user_service):
    email = f"other-user-human-reviews-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def admin_user(user_service):
    # is_staff=True is sufficient for AdminPermission / RoleChecker.is_staff
    email = f"admin-human-reviews-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="adminpass123")
    user_service.update_user(user, role="admin", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def reviewer_user(user_service):
    email = f"reviewer-human-reviews-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="reviewerpass123")
    user_service.update_user(user, role="reviewer", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def reviewer_user_not_staff(user_service):
    """
    Reviewer role but not staff/admin - used to validate service-layer guardrails.
    """
    email = f"reviewer-nonstaff-human-reviews-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="reviewerpass123")
    user_service.update_user(user, role="reviewer", is_staff=False)
    user_service.activate_user(user)
    return user


# -----------------------------------------------------------------------------
# Domain object fixtures (created through services when available)
# -----------------------------------------------------------------------------

@pytest.fixture
def paid_case(case_service, payment_service, case_owner) -> Tuple[object, object]:
    """
    Returns: (case, payment)

    Payment is created (pre-case) and completed, then attached to the case during case creation.
    Mirrors src/immigration_cases/tests/conftest.py.
    """
    payment = payment_service.create_payment(
        user_id=str(case_owner.id),
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        payment_provider="stripe",
        provider_transaction_id=f"txn_hr_{uuid.uuid4().hex[:8]}",
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

    # Important: PaymentValidator caches per-case validation results. Since the payment
    # was completed before it was attached to the case, invalidate the per-case cache
    # to ensure downstream services see the attached completed payment immediately.
    from payments.helpers.payment_validator import PaymentValidator

    PaymentValidator.invalidate_payment_cache(str(case.id))
    return case, payment


@pytest.fixture
def case_without_completed_payment(paid_case, payment_service, case_owner):
    """
    Create a valid case then soft-delete the attached payment,
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
def visa_type(visa_type_service, paid_case):
    case, _payment = paid_case
    code = f"US_HR_{uuid.uuid4().hex[:6]}".upper()
    vt = visa_type_service.create_visa_type(
        jurisdiction=case.jurisdiction,
        code=code,
        name="Test Visa Type (human_reviews)",
        description="Test visa type for human_reviews tests",
        is_active=True,
    )
    assert vt is not None
    return vt


@pytest.fixture
def rule_version(visa_rule_version_service, visa_type, admin_user):
    rv = visa_rule_version_service.create_rule_version(
        visa_type_id=str(visa_type.id),
        effective_from=timezone.now(),
        effective_to=None,
        source_document_version_id=None,
        is_published=True,
        created_by=admin_user,
    )
    assert rv is not None
    return rv


@pytest.fixture
def eligibility_result(eligibility_result_service, paid_case, visa_type, rule_version):
    case, _payment = paid_case
    result = eligibility_result_service.create_eligibility_result(
        case_id=str(case.id),
        visa_type_id=str(visa_type.id),
        rule_version_id=str(rule_version.id),
        outcome="eligible",
        confidence=0.85,
        reasoning_summary="Test reasoning summary",
        missing_facts={"missing": ["some_fact"]},
    )
    assert result is not None
    return result


@pytest.fixture(autouse=True)
def _isolate_human_reviews_side_effects(monkeypatch):
    """
    Isolate side-effects for human_reviews:
    - Notifications and email tasks emitted by signals
    - Metrics tracking and audit logging
    """
    from users_access.services import notification_service as notification_service_module
    from users_access.tasks import email_tasks as email_tasks_module

    monkeypatch.setattr(
        notification_service_module.NotificationService,
        "create_notification",
        MagicMock(name="NotificationService.create_notification"),
    )
    monkeypatch.setattr(
        email_tasks_module.send_review_assignment_email_task,
        "delay",
        MagicMock(name="send_review_assignment_email_task.delay"),
    )
    monkeypatch.setattr(
        email_tasks_module.send_review_completed_email_task,
        "delay",
        MagicMock(name="send_review_completed_email_task.delay"),
    )
    # ai_decisions signals can emit eligibility-result emails; keep tests deterministic.
    monkeypatch.setattr(
        email_tasks_module.send_eligibility_result_email_task,
        "delay",
        MagicMock(name="send_eligibility_result_email_task.delay"),
    )

    # Payments side-effects (Celery tasks): keep tests deterministic and fast.
    try:
        from payments.tasks import payment_tasks as payment_tasks_module

        monkeypatch.setattr(
            payment_tasks_module.send_payment_notification_task,
            "delay",
            MagicMock(name="send_payment_notification_task.delay"),
        )
    except Exception:
        pass

    # Metrics / audit (keep tests deterministic and fast)
    from human_reviews.helpers import metrics as hr_metrics

    monkeypatch.setattr(hr_metrics, "track_review_creation", MagicMock(name="track_review_creation"))
    monkeypatch.setattr(hr_metrics, "track_review_assignment", MagicMock(name="track_review_assignment"))
    monkeypatch.setattr(hr_metrics, "track_review_status_transition", MagicMock(name="track_review_status_transition"))
    monkeypatch.setattr(hr_metrics, "track_review_version_conflict", MagicMock(name="track_review_version_conflict"))

    from compliance.services import audit_log_service as audit_log_service_module

    monkeypatch.setattr(audit_log_service_module.AuditLogService, "create_audit_log", MagicMock(name="create_audit_log"))

    return True

