"""
Tests for DocumentTypeService.
All tests use services, not direct model access.
"""

import pytest


@pytest.mark.django_db
class TestDocumentTypeService:
    def test_create_document_type_success(self, document_type_service):
        dt = document_type_service.create_document_type(code="NIN", name="National Insurance Number")
        assert dt is not None
        assert dt.code == "NIN"
        assert dt.name == "National Insurance Number"
        assert dt.is_active is True

    def test_create_document_type_duplicate_code_returns_none(self, document_type_service, document_type):
        duplicate = document_type_service.create_document_type(code=document_type.code, name="Duplicate")
        assert duplicate is None

    def test_get_all_and_get_active(self, document_type_service, document_type, inactive_document_type):
        all_qs = document_type_service.get_all()
        active_qs = document_type_service.get_active()
        assert all_qs.count() >= 2
        assert active_qs.filter(id=document_type.id).exists() is True
        assert active_qs.filter(id=inactive_document_type.id).exists() is False

    def test_get_by_code_found_and_not_found(self, document_type_service, document_type):
        found = document_type_service.get_by_code(document_type.code)
        assert found is not None
        assert found.id == document_type.id

        missing = document_type_service.get_by_code("DOES_NOT_EXIST")
        assert missing is None

    def test_get_by_id_found_and_not_found(self, document_type_service, document_type):
        found = document_type_service.get_by_id(str(document_type.id))
        assert found is not None
        assert found.code == document_type.code

        from uuid import uuid4

        missing = document_type_service.get_by_id(str(uuid4()))
        assert missing is None

    def test_update_document_type_success(self, document_type_service, document_type):
        updated = document_type_service.update_document_type(str(document_type.id), name="Passport Updated")
        assert updated is not None
        assert updated.name == "Passport Updated"

    def test_update_document_type_not_found_returns_none(self, document_type_service):
        from uuid import uuid4

        updated = document_type_service.update_document_type(str(uuid4()), name="X")
        assert updated is None

    def test_activate_document_type_success(self, document_type_service, document_type):
        updated = document_type_service.activate_document_type(document_type, False)
        assert updated is not None
        assert updated.is_active is False

        updated2 = document_type_service.activate_document_type(document_type, True)
        assert updated2 is not None
        assert updated2.is_active is True

    def test_delete_document_type_success_and_not_found(self, document_type_service, document_type):
        ok = document_type_service.delete_document_type(str(document_type.id))
        assert ok is True

        # now not found
        ok2 = document_type_service.delete_document_type(str(document_type.id))
        assert ok2 is False

    def test_get_by_filters(self, document_type_service, document_type, inactive_document_type):
        active = document_type_service.get_by_filters(is_active=True)
        inactive = document_type_service.get_by_filters(is_active=False)
        assert active.filter(id=document_type.id).exists() is True
        assert inactive.filter(id=inactive_document_type.id).exists() is True

