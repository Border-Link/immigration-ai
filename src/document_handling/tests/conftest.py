"""
Shared fixtures for document_handling tests.

Constraints:
- Avoid direct Model.objects usage in tests.
- Create state through services and/or API, and mock external integrations.
"""

import pytest

from users_access.services.user_service import UserService
from immigration_cases.services.case_service import CaseService
from rules_knowledge.services.document_type_service import DocumentTypeService

from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService


@pytest.fixture(autouse=True)
def _bypass_payment_validation(monkeypatch):
    """
    Most document_handling operations are gated by payment validation.
    For unit/integration tests of document_handling, we bypass that gate
    to focus on document handling behavior.
    """
    from payments.helpers import payment_validator

    monkeypatch.setattr(
        payment_validator.PaymentValidator,
        "validate_case_has_payment",
        lambda *args, **kwargs: (True, None),
        raising=True,
    )
    monkeypatch.setattr(
        payment_validator.PaymentValidator,
        "can_create_case_for_user",
        lambda *args, **kwargs: (True, None),
        raising=True,
    )

    # Avoid touching payments service during CaseService.create_case()
    from payments.selectors import payment_selector

    class _EmptyQS:
        def first(self):
            return None

    monkeypatch.setattr(
        payment_selector.PaymentSelector,
        "get_unassigned_completed_by_user",
        lambda *args, **kwargs: _EmptyQS(),
        raising=True,
    )


@pytest.fixture
def user_service():
    return UserService


@pytest.fixture
def case_service():
    return CaseService


@pytest.fixture
def document_type_service():
    return DocumentTypeService


@pytest.fixture
def case_document_service():
    return CaseDocumentService


@pytest.fixture
def document_check_service():
    return DocumentCheckService


@pytest.fixture
def test_user(user_service):
    return user_service.create_user(email="dh-user@example.com", password="TestPass123!@#")


@pytest.fixture
def other_user(user_service):
    return user_service.create_user(email="dh-other@example.com", password="TestPass123!@#")


@pytest.fixture
def admin_user(user_service):
    return user_service.create_superuser(email="dh-admin@example.com", password="AdminPass123!@#")


@pytest.fixture
def test_case(case_service, test_user):
    # CaseService requires a "jurisdiction" string, and payment is bypassed via autouse fixture.
    case = case_service.create_case(user_id=str(test_user.id), jurisdiction="UK", status="draft")
    assert case is not None
    return case


@pytest.fixture
def other_case(case_service, other_user):
    case = case_service.create_case(user_id=str(other_user.id), jurisdiction="UK", status="draft")
    assert case is not None
    return case


@pytest.fixture
def active_document_type(document_type_service):
    # Use unique code to avoid collisions across parallel tests.
    import uuid

    code = f"passport_{uuid.uuid4().hex[:8]}"
    doc_type = document_type_service.create_document_type(code=code, name="Passport", description="Test passport", is_active=True)
    assert doc_type is not None
    return doc_type


@pytest.fixture
def inactive_document_type(document_type_service):
    import uuid

    code = f"inactive_{uuid.uuid4().hex[:8]}"
    doc_type = document_type_service.create_document_type(code=code, name="Inactive", description="Inactive type", is_active=False)
    assert doc_type is not None
    return doc_type


@pytest.fixture
def case_document(case_document_service, test_case, active_document_type):
    doc = case_document_service.create_case_document(
        case_id=str(test_case.id),
        document_type_id=str(active_document_type.id),
        file_path="case_documents/test/test.pdf",
        file_name="test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status="uploaded",
    )
    assert doc is not None
    return doc


@pytest.fixture
def document_check(document_check_service, case_document):
    check = document_check_service.create_document_check(
        case_document_id=str(case_document.id),
        check_type="ocr",
        result="passed",
        details={"ok": True},
        performed_by="pytest",
    )
    assert check is not None
    return check

