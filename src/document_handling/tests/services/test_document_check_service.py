"""
Tests for DocumentCheckService.

Focus:
- Happy paths (create/read/update/delete)
- Payment gating (patched in conftest, overridden in specific tests)
- Filtering APIs and statistics
"""

import pytest


@pytest.mark.django_db
class TestDocumentCheckService:
    def test_create_document_check_success(self, document_check_service, case_document):
        check = document_check_service.create_document_check(
            case_document_id=str(case_document.id),
            check_type="classification",
            result="warning",
            details={"confidence": 0.55},
            performed_by="pytest",
        )
        assert check is not None
        assert check.check_type == "classification"
        assert check.result == "warning"

    def test_create_document_check_missing_case_document_returns_none(self, document_check_service):
        from uuid import uuid4

        check = document_check_service.create_document_check(
            case_document_id=str(uuid4()),
            check_type="ocr",
            result="passed",
        )
        assert check is None

    def test_create_document_check_payment_invalid_returns_none(self, monkeypatch, document_check_service, case_document):
        from payments.helpers import payment_validator

        monkeypatch.setattr(
            payment_validator.PaymentValidator,
            "validate_case_has_payment",
            lambda *args, **kwargs: (False, "payment required"),
            raising=True,
        )
        check = document_check_service.create_document_check(
            case_document_id=str(case_document.id),
            check_type="ocr",
            result="passed",
        )
        assert check is None

    def test_get_by_id_success(self, document_check_service, document_check):
        found = document_check_service.get_by_id(str(document_check.id))
        assert found is not None
        assert str(found.id) == str(document_check.id)

    def test_get_by_id_not_found_returns_none(self, document_check_service):
        from uuid import uuid4

        found = document_check_service.get_by_id(str(uuid4()))
        assert found is None

    def test_get_all(self, document_check_service, document_check):
        qs = document_check_service.get_all()
        assert qs.count() >= 1

    def test_get_by_case_document(self, document_check_service, case_document, document_check):
        qs = document_check_service.get_by_case_document(str(case_document.id))
        assert qs.count() >= 1

    def test_get_by_check_type(self, document_check_service, document_check):
        qs = document_check_service.get_by_check_type("ocr")
        assert qs.count() >= 1

    def test_get_by_result(self, document_check_service, document_check):
        qs = document_check_service.get_by_result("passed")
        assert qs.count() >= 1

    def test_get_latest_by_case_document(self, document_check_service, case_document, document_check):
        latest = document_check_service.get_latest_by_case_document(str(case_document.id), check_type="ocr")
        assert latest is not None
        assert latest.check_type == "ocr"

    def test_update_document_check_success(self, document_check_service, document_check):
        updated = document_check_service.update_document_check(str(document_check.id), result="warning")
        assert updated is not None
        assert updated.result == "warning"

    def test_update_document_check_not_found_returns_none(self, document_check_service):
        from uuid import uuid4

        updated = document_check_service.update_document_check(str(uuid4()), result="warning")
        assert updated is None

    def test_delete_document_check_success(self, document_check_service, document_check):
        ok = document_check_service.delete_document_check(str(document_check.id))
        assert ok is True
        assert document_check_service.get_by_id(str(document_check.id)) is None

    def test_delete_document_check_not_found_returns_false(self, document_check_service):
        from uuid import uuid4

        ok = document_check_service.delete_document_check(str(uuid4()))
        assert ok is False

    def test_get_by_filters(self, document_check_service, case_document, document_check):
        qs = document_check_service.get_by_filters(case_document_id=str(case_document.id), check_type="ocr")
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, document_check_service, document_check):
        stats = document_check_service.get_statistics()
        assert isinstance(stats, dict)
        assert "total" in stats

