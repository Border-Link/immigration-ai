"""
Pytest configuration and shared fixtures for ai_decisions tests.

Conventions (aligned with users_access + immigration_cases):
- Do not call Django models directly in tests; use services as the entrypoint.
- Keep side-effects (email tasks, notifications, metrics, audit logging) isolated via mocks.
- Clear shared cache between tests to avoid coupling due to @cache_result usage.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Tuple, List, Dict
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
from ai_decisions.services import (
    EligibilityResultService,
    AIReasoningLogService,
    AICitationService,
    PgVectorService,
)


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
def ai_reasoning_log_service():
    return AIReasoningLogService


@pytest.fixture
def ai_citation_service():
    return AICitationService


@pytest.fixture
def pgvector_service():
    return PgVectorService


# -----------------------------------------------------------------------------
# User fixtures (roles align with RoleChecker/AdminPermission)
# -----------------------------------------------------------------------------

@pytest.fixture
def case_owner(user_service):
    email = f"case-owner-ai-decisions-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def other_user(user_service):
    email = f"other-user-ai-decisions-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="testpass123")
    user_service.activate_user(user)
    return user


@pytest.fixture
def admin_user(user_service):
    # is_staff=True is sufficient for AdminPermission / RoleChecker.is_staff
    email = f"admin-ai-decisions-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="adminpass123")
    user_service.update_user(user, role="admin", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def reviewer_user(user_service):
    email = f"reviewer-ai-decisions-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="reviewerpass123")
    user_service.update_user(user, role="reviewer", is_staff=True)
    user_service.activate_user(user)
    return user


@pytest.fixture
def superadmin_user(user_service):
    email = f"superadmin-ai-decisions-{uuid.uuid4().hex[:8]}@example.com"
    return user_service.create_superuser(email=email, password="adminpass123")


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
        provider_transaction_id=f"txn_ai_decisions_{uuid.uuid4().hex[:8]}",
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
def visa_type(visa_type_service, paid_case):
    case, _payment = paid_case
    code = f"US_TEST_{uuid.uuid4().hex[:6]}".upper()
    vt = visa_type_service.create_visa_type(
        jurisdiction=case.jurisdiction,
        code=code,
        name="Test Visa Type",
        description="Test visa type for ai_decisions tests",
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


# -----------------------------------------------------------------------------
# Data ingestion fixtures for citations / vector search (created via services)
# -----------------------------------------------------------------------------

@pytest.fixture
def document_version():
    """
    Create a minimal DocumentVersion + SourceDocument + DataSource.

    We use repository setup for SourceDocument/DocumentVersion because these apps
    do not consistently expose service create APIs for every model.
    """
    from data_ingestion.services.data_source_service import DataSourceService
    from data_ingestion.repositories.source_document_repository import SourceDocumentRepository
    from data_ingestion.repositories.document_version_repository import DocumentVersionRepository

    data_source = DataSourceService.create_data_source(
        name=f"AI Decisions Data Source {uuid.uuid4().hex[:6]}",
        base_url="https://www.gov.uk/api/content/example",
        jurisdiction="US",
        crawl_frequency="weekly",
        is_active=True,
    )
    assert data_source is not None

    source_document = SourceDocumentRepository.create_source_document(
        data_source=data_source,
        source_url="https://www.gov.uk/api/content/example-doc",
        raw_content='{"title":"Example","content_id":"cid"}',
        content_type="application/json",
        http_status_code=200,
    )
    assert source_document is not None

    doc_version = DocumentVersionRepository.create_document_version(
        source_document=source_document,
        raw_text="Eligibility guidance: Applicant must have job offer. Fee is $100.",
        metadata={"content_id": "cid", "base_path": "/example"},
    )
    assert doc_version is not None
    return doc_version


@pytest.fixture
def document_chunks(document_version) -> List:
    """Create DocumentChunk rows via PgVectorService (service entrypoint)."""
    chunks: List[Dict] = [
        {"text": "Chunk A. Applicant must have a job offer.", "metadata": {"chunk_index": 0, "visa_code": "US_TEST"}},
        {"text": "Chunk B. Fees and processing times.", "metadata": {"chunk_index": 1, "visa_code": "US_TEST"}},
    ]
    embeddings: List[List[float]] = [[0.0] * 1536, [0.1] * 1536]
    created = PgVectorService.store_chunks(document_version=document_version, chunks=chunks, embeddings=embeddings)
    assert created is not None
    return created


@pytest.fixture
def reasoning_log(ai_reasoning_log_service, paid_case):
    case, _payment = paid_case
    log = ai_reasoning_log_service.create_reasoning_log(
        case_id=str(case.id),
        prompt="Test prompt",
        response="Test response",
        model_name="test-model",
        tokens_used=123,
    )
    assert log is not None
    return log


@pytest.fixture
def citation(ai_citation_service, reasoning_log, document_version):
    c = ai_citation_service.create_citation(
        reasoning_log_id=str(reasoning_log.id),
        document_version_id=str(document_version.id),
        excerpt="Example excerpt",
        relevance_score=0.9,
    )
    assert c is not None
    return c


# -----------------------------------------------------------------------------
# Global side-effect isolation (signals, Celery task dispatch)
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_ai_decisions_side_effects(monkeypatch):
    """
    Isolate side-effects for ai_decisions:
    - Notifications and email tasks emitted by signals
    - Auto review creation
    """
    from users_access.services import notification_service as notification_service_module
    from users_access.tasks import email_tasks as email_tasks_module
    from human_reviews.services import review_service as review_service_module

    monkeypatch.setattr(
        notification_service_module.NotificationService,
        "create_notification",
        MagicMock(name="NotificationService.create_notification"),
    )
    monkeypatch.setattr(
        email_tasks_module.send_eligibility_result_email_task,
        "delay",
        MagicMock(name="send_eligibility_result_email_task.delay"),
    )
    monkeypatch.setattr(
        review_service_module.ReviewService,
        "create_review",
        MagicMock(name="ReviewService.create_review"),
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
        # If payments.tasks isn't available in this test environment, ignore.
        pass

