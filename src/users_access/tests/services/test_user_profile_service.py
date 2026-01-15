"""
Tests for UserProfileService.
All tests use services, not direct model access.
"""
import pytest
from datetime import date
from users_access.services.user_profile_service import UserProfileService


@pytest.mark.django_db
class TestUserProfileService:
    """Tests for UserProfileService."""

    def test_get_profile(self, user_profile_service, test_user):
        """Test getting profile."""
        profile = user_profile_service.get_profile(test_user)
        assert profile is not None
        assert profile.user == test_user

    def test_get_profile_creates_if_not_exists(self, user_profile_service, test_user):
        """Test profile is created if doesn't exist."""
        # Profile should be auto-created by signal, but test the service method
        profile = user_profile_service.get_profile(test_user)
        assert profile is not None

    def test_update_profile(self, user_profile_service, test_user):
        """Test updating profile."""
        profile = user_profile_service.update_profile(
            test_user,
            first_name="Jane",
            last_name="Smith"
        )
        assert profile.first_name == "Jane"
        assert profile.last_name == "Smith"

    def test_update_names(self, user_profile_service, test_user):
        """Test updating names."""
        updated = user_profile_service.update_names(
            test_user,
            first_name="John",
            last_name="Doe"
        )
        assert updated.first_name == "John"
        assert updated.last_name == "Doe"

    def test_update_nationality(self, user_profile_service, test_user, test_country):
        """Test updating nationality."""
        updated = user_profile_service.update_nationality(
            test_user,
            "US"
        )
        assert updated.nationality == test_country

    def test_update_nationality_with_state(self, user_profile_service, test_user, test_country, test_state_province):
        """Test updating nationality with state."""
        updated = user_profile_service.update_nationality(
            test_user,
            "US",
            "CA"
        )
        assert updated.nationality == test_country
        assert updated.state_province == test_state_province

    def test_update_consent(self, user_profile_service, test_user):
        """Test updating consent."""
        updated = user_profile_service.update_consent(test_user, True)
        assert updated.consent_given is True
        assert updated.consent_timestamp is not None

    def test_update_consent_false(self, user_profile_service, test_user):
        """Test revoking consent."""
        user_profile_service.update_consent(test_user, True)
        updated = user_profile_service.update_consent(test_user, False)
        assert updated.consent_given is False
        assert updated.consent_timestamp is None

    def test_update_avatar(self, user_profile_service, test_user):
        """Test updating avatar."""
        from unittest.mock import MagicMock
        mock_avatar = MagicMock()
        updated = user_profile_service.update_avatar(test_user, mock_avatar)
        assert updated is not None

    def test_remove_avatar(self, user_profile_service, test_user):
        """Test removing avatar."""
        result = user_profile_service.remove_avatar(test_user)
        # Should return None if no avatar exists
        assert result is None

    def test_get_by_filters(self, user_profile_service, test_user, test_country):
        """Test getting profiles with filters."""
        user_profile_service.update_nationality(test_user, "US")
        profiles = user_profile_service.get_by_filters(nationality="US")
        assert profiles.count() >= 1

    def test_get_by_filters_user_id(self, user_profile_service, test_user):
        """Test getting profile by user ID filter."""
        profiles = user_profile_service.get_by_filters(user_id=str(test_user.id))
        assert profiles.count() == 1

    def test_get_by_filters_consent(self, user_profile_service, test_user):
        """Test getting profiles by consent filter."""
        user_profile_service.update_consent(test_user, True)
        profiles = user_profile_service.get_by_filters(consent_given=True)
        assert profiles.count() >= 1

    def test_update_nationality_invalid_code(self, user_profile_service, test_user):
        """Test updating nationality with invalid country code."""
        result = user_profile_service.update_nationality(test_user, "XX")
        assert result is None

    def test_update_nationality_invalid_state(self, user_profile_service, test_user, test_country):
        """Test updating nationality with invalid state code."""
        result = user_profile_service.update_nationality(test_user, test_country.code, "XX")
        assert result is None

    def test_update_names_empty_strings(self, user_profile_service, test_user):
        """Test updating names with empty strings."""
        updated = user_profile_service.update_names(test_user, "", "")
        assert updated is not None

    def test_update_names_none(self, user_profile_service, test_user):
        """Test updating names with None values."""
        updated = user_profile_service.update_names(test_user, None, None)
        assert updated is not None

    def test_update_profile_empty_data(self, user_profile_service, test_user):
        """Test updating profile with empty data."""
        profile = user_profile_service.update_profile(test_user)
        assert profile is not None
