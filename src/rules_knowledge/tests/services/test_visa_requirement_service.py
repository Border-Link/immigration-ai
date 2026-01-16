"""
Tests for VisaRequirementService.
All tests use services, not direct model access.
"""

import pytest


@pytest.mark.django_db
class TestVisaRequirementService:
    def test_create_visa_requirement_maps_is_active_to_is_mandatory(
        self, visa_requirement_service, rule_version_unpublished
    ):
        req = visa_requirement_service.create_visa_requirement(
            rule_version_id=str(rule_version_unpublished.id),
            requirement_code="MIN_SALARY",
            description="Salary must be at least 30000",
            condition_expression={">=": [{"var": "salary"}, 30000]},
            is_active=False,  # maps to is_mandatory=False
        )
        assert req is not None
        assert req.rule_type == "eligibility"
        assert req.is_mandatory is False

    def test_create_visa_requirement_invalid_json_logic_returns_none(
        self, visa_requirement_service, rule_version_unpublished
    ):
        # Invalid operator -> JSONLogicValidator rejects
        req = visa_requirement_service.create_visa_requirement(
            rule_version_id=str(rule_version_unpublished.id),
            requirement_code="BAD_EXPR",
            description="Bad expression",
            condition_expression={"not_a_valid_operator": [1, 2]},
            is_active=True,
        )
        assert req is None

    def test_get_all_and_get_by_rule_version(
        self, visa_requirement_service, visa_requirement, rule_version_unpublished
    ):
        assert visa_requirement_service.get_all().filter(id=visa_requirement.id).exists() is True
        assert (
            visa_requirement_service.get_by_rule_version(str(rule_version_unpublished.id))
            .filter(id=visa_requirement.id)
            .exists()
            is True
        )

    def test_get_by_id_found_and_not_found(self, visa_requirement_service, visa_requirement):
        found = visa_requirement_service.get_by_id(str(visa_requirement.id))
        assert found is not None
        assert found.requirement_code == visa_requirement.requirement_code

        from uuid import uuid4

        assert visa_requirement_service.get_by_id(str(uuid4())) is None

    def test_update_visa_requirement_maps_is_active(self, visa_requirement_service, visa_requirement):
        updated = visa_requirement_service.update_visa_requirement(
            str(visa_requirement.id),
            is_active=False,
        )
        assert updated is not None
        assert updated.is_mandatory is False

    def test_update_requirement_invalid_expression_returns_none(self, visa_requirement_service, visa_requirement):
        updated = visa_requirement_service.update_requirement(
            str(visa_requirement.id),
            condition_expression={"bad_operator": [1, 2]},
        )
        assert updated is None

    def test_delete_requirement_success_and_not_found(self, visa_requirement_service, visa_requirement):
        ok = visa_requirement_service.delete_requirement(str(visa_requirement.id))
        assert ok is True
        ok2 = visa_requirement_service.delete_requirement(str(visa_requirement.id))
        assert ok2 is False

