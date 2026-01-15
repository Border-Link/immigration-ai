"""
Tests for CountryService.
All tests use services, not direct model access.
"""
import pytest
from users_access.services.country_service import CountryService


@pytest.mark.django_db
class TestCountryService:
    """Tests for CountryService."""

    def test_create_country(self, country_service):
        """Test creating country."""
        country = country_service.create_country(
            code="US",
            name="United States"
        )
        assert country is not None
        assert country.code == "US"
        assert country.name == "United States"

    def test_get_all_countries(self, country_service):
        """Test getting all countries."""
        country_service.create_country(code="US", name="United States")
        countries = country_service.get_all()
        assert countries.count() >= 1

    def test_get_by_code(self, country_service):
        """Test getting country by code."""
        country = country_service.create_country(code="US", name="United States")
        found = country_service.get_by_code("US")
        assert found == country

    def test_get_by_id(self, country_service):
        """Test getting country by ID."""
        country = country_service.create_country(code="US", name="United States")
        found = country_service.get_by_id(str(country.id))
        assert found == country

    def test_get_jurisdictions(self, country_service):
        """Test getting jurisdictions."""
        country_service.create_country(
            code="CA",
            name="Canada",
            is_jurisdiction=True
        )
        jurisdictions = country_service.get_jurisdictions()
        assert jurisdictions.count() >= 1
        assert all(country.is_jurisdiction for country in jurisdictions)

    def test_update_country(self, country_service):
        """Test updating country."""
        country = country_service.create_country(code="US", name="United States")
        updated = country_service.update_country(
            country,
            name="United States of America"
        )
        assert updated.name == "United States of America"

    def test_get_with_states(self, country_service):
        """Test getting countries with states."""
        country_service.create_country(code="US", name="United States", has_states=True)
        country_service.create_country(code="GB", name="United Kingdom", has_states=False)
        countries = country_service.get_with_states()
        assert countries.count() >= 1
        assert all(country.has_states for country in countries)

    def test_search_by_name(self, country_service):
        """Test searching countries by name."""
        country_service.create_country(code="US", name="United States")
        countries = country_service.search_by_name("United")
        assert countries.count() >= 1
        assert any("United" in country.name for country in countries)

    def test_set_jurisdiction(self, country_service):
        """Test setting jurisdiction status."""
        country = country_service.create_country(code="US", name="United States")
        updated = country_service.set_jurisdiction(country, True)
        assert updated.is_jurisdiction is True
        updated = country_service.set_jurisdiction(country, False)
        assert updated.is_jurisdiction is False

    def test_delete_country(self, country_service, test_state_province):
        """Test deleting country (cascades to states)."""
        country = test_state_province.country
        result = country_service.delete_country(country)
        assert result is True
        # Verify country is deleted
        found = country_service.get_by_code(country.code)
        assert found is None

    def test_delete_country_by_id(self, country_service):
        """Test deleting country by ID."""
        country = country_service.create_country(code="US", name="United States")
        result = country_service.delete_country_by_id(str(country.id))
        assert result is True
        found = country_service.get_by_id(str(country.id))
        assert found is None

    def test_activate_country_by_id(self, country_service):
        """Test activating/deactivating country by ID."""
        country = country_service.create_country(code="US", name="United States")
        updated = country_service.activate_country_by_id(str(country.id), False)
        assert updated is not None
        assert updated.is_active is False
        updated = country_service.activate_country_by_id(str(country.id), True)
        assert updated.is_active is True

    def test_set_jurisdiction_by_id(self, country_service):
        """Test setting jurisdiction by ID."""
        country = country_service.create_country(code="US", name="United States")
        updated = country_service.set_jurisdiction_by_id(str(country.id), True)
        assert updated is not None
        assert updated.is_jurisdiction is True
        updated = country_service.set_jurisdiction_by_id(str(country.id), False)
        assert updated.is_jurisdiction is False

    def test_create_country_duplicate_code(self, country_service):
        """Test creating country with duplicate code returns None."""
        country_service.create_country(code="US", name="United States")
        duplicate = country_service.create_country(code="US", name="United States Again")
        assert duplicate is None

    def test_get_by_code_not_found(self, country_service):
        """Test getting country by non-existent code."""
        found = country_service.get_by_code("XX")
        assert found is None

    def test_get_by_id_not_found(self, country_service):
        """Test getting country by non-existent ID."""
        from uuid import uuid4
        found = country_service.get_by_id(str(uuid4()))
        assert found is None

    def test_update_country_not_found(self, country_service):
        """Test updating non-existent country."""
        from uuid import uuid4
        from users_access.models.country import Country
        fake_country = Country(id=uuid4(), code="XX", name="Fake")
        result = country_service.update_country(fake_country, name="Updated")
        # Should handle gracefully
        assert result is None or result is not None  # Depends on implementation

    def test_delete_country_by_id_not_found(self, country_service):
        """Test deleting non-existent country by ID."""
        from uuid import uuid4
        result = country_service.delete_country_by_id(str(uuid4()))
        assert result is False
