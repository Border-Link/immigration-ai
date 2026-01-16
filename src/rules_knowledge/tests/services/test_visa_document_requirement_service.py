"""
Tests for VisaDocumentRequirementService.
All tests use services, not direct model access.
"""

import pytest


@pytest.mark.django_db
class TestVisaDocumentRequirementService:
    def test_create_visa_document_requirement_success_and_description_mapping(
        self, visa_document_requirement_service, rule_version_unpublished, document_type
    ):
        req = visa_document_requirement_service.create_visa_document_requirement(
            rule_version_id=str(rule_version_unpublished.id),
            document_type_id=str(document_type.id),
            mandatory=True,
            description="Passport required",
        )
        assert req is not None
        assert req.mandatory is True
        assert isinstance(req.conditional_logic, dict)
        assert req.conditional_logic.get("description") == "Passport required"

    def test_create_visa_document_requirement_duplicate_returns_none(
        self, visa_document_requirement_service, visa_document_requirement, rule_version_unpublished, document_type
    ):
        dup = visa_document_requirement_service.create_visa_document_requirement(
            rule_version_id=str(rule_version_unpublished.id),
            document_type_id=str(document_type.id),
            mandatory=True,
            description="Dup",
        )
        assert dup is None

    def test_get_all_and_get_by_rule_version(
        self, visa_document_requirement_service, visa_document_requirement, rule_version_unpublished
    ):
        assert visa_document_requirement_service.get_all().filter(id=visa_document_requirement.id).exists() is True
        assert (
            visa_document_requirement_service.get_by_rule_version(str(rule_version_unpublished.id))
            .filter(id=visa_document_requirement.id)
            .exists()
            is True
        )

    def test_get_by_id_found_and_not_found(self, visa_document_requirement_service, visa_document_requirement):
        found = visa_document_requirement_service.get_by_id(str(visa_document_requirement.id))
        assert found is not None
        assert found.id == visa_document_requirement.id

        from uuid import uuid4

        assert visa_document_requirement_service.get_by_id(str(uuid4())) is None

    def test_update_visa_document_requirement_maps_description(
        self, visa_document_requirement_service, visa_document_requirement
    ):
        updated = visa_document_requirement_service.update_visa_document_requirement(
            str(visa_document_requirement.id),
            description="Updated description",
        )
        assert updated is not None
        assert isinstance(updated.conditional_logic, dict)
        assert updated.conditional_logic.get("description") == "Updated description"

    def test_update_document_requirement_updates_mandatory(self, visa_document_requirement_service, visa_document_requirement):
        updated = visa_document_requirement_service.update_document_requirement(
            str(visa_document_requirement.id),
            mandatory=False,
        )
        assert updated is not None
        assert updated.mandatory is False

    def test_delete_document_requirement_success_and_not_found(
        self, visa_document_requirement_service, visa_document_requirement
    ):
        ok = visa_document_requirement_service.delete_document_requirement(str(visa_document_requirement.id))
        assert ok is True
        ok2 = visa_document_requirement_service.delete_document_requirement(str(visa_document_requirement.id))
        assert ok2 is False

