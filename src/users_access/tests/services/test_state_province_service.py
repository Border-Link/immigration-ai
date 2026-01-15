"""
Tests for StateProvinceService.
All tests use services, not direct model access.
"""
import pytest
from users_access.services.state_province_service import StateProvinceService


@pytest.mark.django_db
class TestStateProvinceService:
    """Tests for StateProvinceService."""

    def test_create_state_province(self, state_province_service, test_country):
        """Test creating state/province."""
        state = state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="CA",
            name="California"
        )
        assert state is not None
        assert state.code == "CA"
        assert state.name == "California"

    def test_get_by_country(self, state_province_service, test_country):
        """Test getting states by country."""
        state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="CA",
            name="California"
        )
        states = state_province_service.get_by_country(str(test_country.id))
        assert states.count() >= 1

    def test_get_by_country_id(self, state_province_service, test_country):
        """Test getting states by country ID."""
        state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="NY",
            name="New York"
        )
        states = state_province_service.get_by_country_id(str(test_country.id))
        assert states.count() >= 1

    def test_get_nomination_programs(self, state_province_service, test_country):
        """Test getting states with nomination programs."""
        state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="ON",
            name="Ontario",
            has_nomination_program=True
        )
        states = state_province_service.get_nomination_programs(str(test_country.id))
        assert states.count() >= 1
        assert all(state.has_nomination_program for state in states)

    def test_update_state_province(self, state_province_service, test_state_province):
        """Test updating state/province."""
        updated = state_province_service.update_state_province(
            test_state_province,
            name="Californie"
        )
        assert updated.name == "Californie"

    def test_get_by_code(self, state_province_service, test_country):
        """Test getting state by country code and state code."""
        state = state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="CA",
            name="California"
        )
        found = state_province_service.get_by_code(test_country.code, "CA")
        assert found == state

    def test_get_by_id(self, state_province_service, test_state_province):
        """Test getting state by ID."""
        found = state_province_service.get_by_id(str(test_state_province.id))
        assert found == test_state_province

    def test_set_nomination_program(self, state_province_service, test_state_province):
        """Test setting nomination program status."""
        updated = state_province_service.set_nomination_program(test_state_province, True)
        assert updated.has_nomination_program is True
        updated = state_province_service.set_nomination_program(test_state_province, False)
        assert updated.has_nomination_program is False

    def test_delete_state_province(self, state_province_service, test_state_province):
        """Test deleting state/province."""
        state_id = test_state_province.id
        result = state_province_service.delete_state_province(test_state_province)
        assert result is True
        # Verify state is deleted
        found = state_province_service.get_by_id(str(state_id))
        assert found is None

    def test_delete_state_province_by_id(self, state_province_service, test_state_province):
        """Test deleting state/province by ID."""
        state_id = test_state_province.id
        result = state_province_service.delete_state_province_by_id(str(state_id))
        assert result is True
        found = state_province_service.get_by_id(str(state_id))
        assert found is None

    def test_activate_state_province_by_id(self, state_province_service, test_state_province):
        """Test activating/deactivating state/province by ID."""
        updated = state_province_service.activate_state_province_by_id(
            str(test_state_province.id), False
        )
        assert updated is not None
        assert updated.is_active is False
        updated = state_province_service.activate_state_province_by_id(
            str(test_state_province.id), True
        )
        assert updated.is_active is True

    def test_get_nomination_programs_no_country_id(self, state_province_service, test_country):
        """Test getting nomination programs without country ID."""
        state_province_service.create_state_province(
            country_id=str(test_country.id),
            code="ON",
            name="Ontario",
            has_nomination_program=True
        )
        states = state_province_service.get_nomination_programs()
        assert states.count() >= 1

    def test_create_state_province_country_no_states(self, state_province_service):
        """Test creating state for country without states returns None."""
        from users_access.services.country_service import CountryService
        country = CountryService.create_country(code="GB", name="United Kingdom", has_states=False)
        result = state_province_service.create_state_province(
            country_id=str(country.id),
            code="EN",
            name="England"
        )
        assert result is None

    def test_get_by_code_not_found(self, state_province_service, test_country):
        """Test getting state by non-existent codes."""
        found = state_province_service.get_by_code(test_country.code, "XX")
        assert found is None

    def test_get_by_id_not_found(self, state_province_service):
        """Test getting state by non-existent ID."""
        from uuid import uuid4
        found = state_province_service.get_by_id(str(uuid4()))
        assert found is None

    def test_delete_state_province_by_id_not_found(self, state_province_service):
        """Test deleting non-existent state by ID."""
        from uuid import uuid4
        result = state_province_service.delete_state_province_by_id(str(uuid4()))
        assert result is False
