"""
Tests for VisaTypeService.
All tests use services, not direct model access.
"""

import pytest


@pytest.mark.django_db
class TestVisaTypeService:
    def test_create_visa_type_success(self, visa_type_service):
        vt = visa_type_service.create_visa_type(
            jurisdiction="UK",
            code="STUDENT",
            name="Student",
            description="Student route",
            is_active=True,
        )
        assert vt is not None
        assert vt.jurisdiction == "UK"
        assert vt.code == "STUDENT"
        assert vt.is_active is True

    def test_create_visa_type_duplicate_returns_none(self, visa_type_service, visa_type_uk):
        duplicate = visa_type_service.create_visa_type(
            jurisdiction=visa_type_uk.jurisdiction,
            code=visa_type_uk.code,
            name="Duplicate",
        )
        assert duplicate is None

    def test_get_all_and_get_active(self, visa_type_service, visa_type_uk, visa_type_us):
        all_qs = visa_type_service.get_all()
        active_qs = visa_type_service.get_active()
        assert all_qs.count() >= 2
        assert active_qs.filter(id=visa_type_uk.id).exists() is True
        assert active_qs.filter(id=visa_type_us.id).exists() is True

    def test_get_by_jurisdiction_returns_only_active(self, visa_type_service, visa_type_uk):
        # Create an inactive one in same jurisdiction
        inactive = visa_type_service.create_visa_type(
            jurisdiction="UK",
            code="TEMP",
            name="Temp",
            is_active=False,
        )
        assert inactive is not None
        qs = visa_type_service.get_by_jurisdiction("UK")
        assert qs.filter(id=visa_type_uk.id).exists() is True
        assert qs.filter(id=inactive.id).exists() is False

    def test_get_by_id_found_and_not_found(self, visa_type_service, visa_type_uk):
        found = visa_type_service.get_by_id(str(visa_type_uk.id))
        assert found is not None
        assert found.code == visa_type_uk.code

        from uuid import uuid4

        missing = visa_type_service.get_by_id(str(uuid4()))
        assert missing is None

    def test_update_visa_type_success(self, visa_type_service, visa_type_uk):
        updated = visa_type_service.update_visa_type(str(visa_type_uk.id), name="Skilled Worker Updated")
        assert updated is not None
        assert updated.name == "Skilled Worker Updated"

    def test_update_visa_type_not_found_returns_none(self, visa_type_service):
        from uuid import uuid4

        updated = visa_type_service.update_visa_type(str(uuid4()), name="X")
        assert updated is None

    def test_activate_visa_type_success(self, visa_type_service, visa_type_uk):
        updated = visa_type_service.activate_visa_type(visa_type_uk, False)
        assert updated is not None
        assert updated.is_active is False

    def test_delete_visa_type_success_and_not_found(self, visa_type_service, visa_type_us):
        ok = visa_type_service.delete_visa_type(str(visa_type_us.id))
        assert ok is True

        ok2 = visa_type_service.delete_visa_type(str(visa_type_us.id))
        assert ok2 is False

    def test_get_by_filters(self, visa_type_service, visa_type_uk, visa_type_us):
        qs = visa_type_service.get_by_filters(jurisdiction="UK")
        assert qs.filter(id=visa_type_uk.id).exists() is True
        assert qs.filter(id=visa_type_us.id).exists() is False

