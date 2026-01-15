"""
Pytest configuration and shared fixtures for users_access tests.
"""
import pytest
from django.contrib.auth import get_user_model
from users_access.services import (
    UserService, UserProfileService, CountryService, StateProvinceService,
    OTPService, UserSettingsService, NotificationService
)

User = get_user_model()


@pytest.fixture
def user_service():
    """Fixture for UserService."""
    return UserService


@pytest.fixture
def user_profile_service():
    """Fixture for UserProfileService."""
    return UserProfileService


@pytest.fixture
def country_service():
    """Fixture for CountryService."""
    return CountryService


@pytest.fixture
def state_province_service():
    """Fixture for StateProvinceService."""
    return StateProvinceService


@pytest.fixture
def otp_service():
    """Fixture for OTPService."""
    return OTPService


@pytest.fixture
def user_settings_service():
    """Fixture for UserSettingsService."""
    return UserSettingsService


@pytest.fixture
def notification_service():
    """Fixture for NotificationService."""
    return NotificationService


@pytest.fixture
def test_user(user_service):
    """Fixture for creating a test user."""
    return user_service.create_user(
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def verified_user(user_service):
    """Fixture for creating a verified test user."""
    user = user_service.create_user(
        email="verified@example.com",
        password="testpass123"
    )
    user_service.activate_user(user)
    return user


@pytest.fixture
def admin_user(user_service):
    """Fixture for creating an admin user."""
    return user_service.create_superuser(
        email="admin@example.com",
        password="adminpass123"
    )


@pytest.fixture
def reviewer_user(user_service):
    """Fixture for creating a reviewer user."""
    user = user_service.create_user(
        email="reviewer@example.com",
        password="reviewerpass123"
    )
    user_service.update_user(user, role='reviewer', is_staff=True)
    return user


@pytest.fixture
def test_country(country_service):
    """Fixture for creating a test country."""
    # Use repository directly for fixture setup since service checks for duplicates
    from users_access.repositories.country_repository import CountryRepository
    return CountryRepository.create_country(
        code="US",
        name="United States",
        has_states=True,
        is_jurisdiction=True,
        is_active=True
    )


@pytest.fixture
def test_state_province(test_country, state_province_service):
    """Fixture for creating a test state/province."""
    # Use repository directly for fixture setup
    from users_access.repositories.state_province_repository import StateProvinceRepository
    return StateProvinceRepository.create_state_province(
        country=test_country,
        code="CA",
        name="California",
        has_nomination_program=True,
        is_active=True
    )


@pytest.fixture
def user_with_profile(test_user, user_profile_service):
    """Fixture for creating a user with profile."""
    user_profile_service.update_names(
        test_user,
        first_name="John",
        last_name="Doe"
    )
    return test_user


@pytest.fixture
def user_with_settings(test_user, user_settings_service):
    """Fixture for creating a user with settings."""
    user_settings_service.create_user_setting(test_user)
    return test_user
