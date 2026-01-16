"""
Tests for CaseDocumentService.

Focus:
- Happy paths (create/read/update/delete)
- Payment-gated behavior (simulated via patching PaymentValidator)
- Failure scenarios (missing case/type, inactive types, repository failures)
"""

import pytest


@pytest.mark.django_db
class TestCaseDocumentService:
    def test_create_case_document_success(self, case_document_service, test_case, active_document_type):
        doc = case_document_service.create_case_document(
            case_id=str(test_case.id),
            document_type_id=str(active_document_type.id),
            file_path="case_documents/x/y/file.pdf",
            file_name="file.pdf",
            file_size=123,
            mime_type="application/pdf",
            status="uploaded",
        )
        assert doc is not None
        assert str(doc.case.id) == str(test_case.id)
        assert str(doc.document_type.id) == str(active_document_type.id)
        assert doc.file_name == "file.pdf"

    def test_create_case_document_inactive_document_type_returns_none(
        self, case_document_service, test_case, inactive_document_type
    ):
        doc = case_document_service.create_case_document(
            case_id=str(test_case.id),
            document_type_id=str(inactive_document_type.id),
            file_path="case_documents/x/y/file.pdf",
            file_name="file.pdf",
        )
        assert doc is None

    def test_create_case_document_case_not_found_returns_none(self, case_document_service, active_document_type):
        from uuid import uuid4

        doc = case_document_service.create_case_document(
            case_id=str(uuid4()),
            document_type_id=str(active_document_type.id),
            file_path="case_documents/x/y/file.pdf",
            file_name="file.pdf",
        )
        assert doc is None

    def test_create_case_document_payment_invalid_returns_none(self, monkeypatch, case_document_service, test_case, active_document_type):
        from payments.helpers import payment_validator

        monkeypatch.setattr(
            payment_validator.PaymentValidator,
            "validate_case_has_payment",
            lambda *args, **kwargs: (False, "payment required"),
            raising=True,
        )
        doc = case_document_service.create_case_document(
            case_id=str(test_case.id),
            document_type_id=str(active_document_type.id),
            file_path="case_documents/x/y/file.pdf",
            file_name="file.pdf",
        )
        assert doc is None

    def test_get_by_id_success(self, case_document_service, case_document):
        found = case_document_service.get_by_id(str(case_document.id))
        assert found is not None
        assert str(found.id) == str(case_document.id)

    def test_get_by_id_not_found_returns_none(self, case_document_service):
        from uuid import uuid4

        found = case_document_service.get_by_id(str(uuid4()))
        assert found is None

    def test_get_all_returns_queryset(self, case_document_service, case_document):
        qs = case_document_service.get_all()
        # Avoid direct ORM assertions; just check it behaves like a queryset/iterable
        assert hasattr(qs, "count")
        assert qs.count() >= 1

    def test_get_by_case_returns_queryset(self, case_document_service, test_case, case_document):
        qs = case_document_service.get_by_case(str(test_case.id))
        assert qs.count() >= 1

    def test_get_by_status_returns_queryset(self, case_document_service, case_document):
        qs = case_document_service.get_by_status("uploaded")
        assert qs.count() >= 1

    def test_update_case_document_success(self, case_document_service, case_document):
        updated = case_document_service.update_case_document(str(case_document.id), file_name="updated.pdf")
        assert updated is not None
        assert updated.file_name == "updated.pdf"

    def test_update_case_document_not_found_returns_none(self, case_document_service):
        from uuid import uuid4

        updated = case_document_service.update_case_document(str(uuid4()), file_name="x.pdf")
        assert updated is None

    def test_update_case_document_payment_invalid_returns_none(self, monkeypatch, case_document_service, case_document):
        from payments.helpers import payment_validator

        monkeypatch.setattr(
            payment_validator.PaymentValidator,
            "validate_case_has_payment",
            lambda *args, **kwargs: (False, "payment required"),
            raising=True,
        )
        updated = case_document_service.update_case_document(str(case_document.id), file_name="x.pdf")
        assert updated is None

    def test_update_status_success(self, case_document_service, case_document):
        updated = case_document_service.update_status(str(case_document.id), "verified")
        assert updated is not None
        assert updated.status == "verified"

    def test_update_status_payment_invalid_returns_none(self, monkeypatch, case_document_service, case_document):
        from payments.helpers import payment_validator

        monkeypatch.setattr(
            payment_validator.PaymentValidator,
            "validate_case_has_payment",
            lambda *args, **kwargs: (False, "payment required"),
            raising=True,
        )
        updated = case_document_service.update_status(str(case_document.id), "verified")
        assert updated is None

    def test_delete_case_document_success(self, monkeypatch, case_document_service, case_document):
        # Ensure storage deletion is attempted but doesn't touch filesystem in unit tests
        from document_handling.services import file_storage_service

        monkeypatch.setattr(file_storage_service.FileStorageService, "delete_file", lambda *args, **kwargs: True, raising=True)
        ok = case_document_service.delete_case_document(str(case_document.id))
        assert ok is True
        assert case_document_service.get_by_id(str(case_document.id)) is None

    def test_delete_case_document_not_found_returns_false(self, case_document_service):
        from uuid import uuid4

        ok = case_document_service.delete_case_document(str(uuid4()))
        assert ok is False

    def test_get_file_url_missing_path_returns_none(self, monkeypatch, case_document_service, case_document):
        # file_path cannot be blank/null due to model validation; patch selector to simulate missing path
        from document_handling.selectors import case_document_selector

        missing_path_doc = type("Doc", (), {"file_path": None})()
        monkeypatch.setattr(case_document_selector.CaseDocumentSelector, "get_by_id", lambda *_: missing_path_doc, raising=True)
        url = case_document_service.get_file_url(str(case_document.id))
        assert url is None

    def test_get_verified_by_case(self, case_document_service, test_case, case_document):
        case_document_service.update_status(str(case_document.id), "verified")
        qs = case_document_service.get_verified_by_case(str(test_case.id))
        assert qs.count() >= 1

    def test_get_statistics_returns_dict(self, case_document_service, case_document):
        stats = case_document_service.get_statistics()
        assert isinstance(stats, dict)
        assert "total" in stats

