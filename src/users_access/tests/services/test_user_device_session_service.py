"""
Tests for UserDeviceSessionService.
All tests use services, not direct model access.
"""
import pytest
from django.utils import timezone
from users_access.services.user_device_session_service import UserDeviceSessionService


@pytest.mark.django_db
class TestUserDeviceSessionService:
    """Tests for UserDeviceSessionService."""

    def test_create_device_session(self, test_user):
        """Test creating device session."""
        session = UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={"os": "iOS"},
            session_id="test_session",
            last_active=timezone.now()
        )
        assert session is not None
        assert session.user == test_user
        assert session.session_id == "test_session"

    def test_revoke_session(self, test_user):
        """Test revoking session."""
        session = UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session",
            last_active=timezone.now()
        )
        result = UserDeviceSessionService.revoke_session("test_session")
        assert result is True
        session.refresh_from_db()
        assert session.revoked is True

    def test_revoke_all_for_user(self, test_user):
        """Test revoking all sessions for user."""
        UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint1",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session1",
            last_active=timezone.now()
        )
        UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint2",
            ip_address="192.168.1.2",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session2",
            last_active=timezone.now()
        )
        result = UserDeviceSessionService.revoke_all_for_user(test_user)
        assert result is True

    def test_mark_active(self, test_user):
        """Test marking session as active."""
        session = UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session",
            last_active=timezone.now()
        )
        original_active = session.last_active
        result = UserDeviceSessionService.mark_active("test_session")
        assert result is True
        session.refresh_from_db()
        assert session.last_active >= original_active

    def test_active_sessions_for_user(self, test_user):
        """Test getting active sessions for user."""
        UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint1",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session1",
            last_active=timezone.now()
        )
        UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint2",
            ip_address="192.168.1.2",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session2",
            last_active=timezone.now()
        )
        sessions = UserDeviceSessionService.active_sessions_for_user(test_user)
        assert len(sessions) >= 2

    def test_get_by_session_id(self, test_user):
        """Test getting session by session ID."""
        session = UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session",
            last_active=timezone.now()
        )
        found = UserDeviceSessionService.get_by_session_id("test_session")
        assert found == session

    def test_get_by_session_id_with_fingerprint(self, test_user):
        """Test getting session by session ID with fingerprint."""
        session = UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session",
            last_active=timezone.now()
        )
        found = UserDeviceSessionService.get_by_session_id("test_session", "test_fingerprint")
        assert found == session

    def test_delete_by_fingerprint(self, test_user):
        """Test deleting session by fingerprint."""
        session = UserDeviceSessionService.create_device_session(
            user=test_user,
            fingerprint="test_fingerprint",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={},
            session_id="test_session",
            last_active=timezone.now()
        )
        result = UserDeviceSessionService.delete_by_fingerprint(test_user, "test_fingerprint")
        assert result is True
        found = UserDeviceSessionService.get_by_session_id("test_session")
        assert found is None

    def test_get_by_session_id_not_found(self, test_user):
        """Test getting non-existent session."""
        found = UserDeviceSessionService.get_by_session_id("nonexistent")
        assert found is None

    def test_revoke_session_not_found(self, test_user):
        """Test revoking non-existent session."""
        result = UserDeviceSessionService.revoke_session("nonexistent")
        assert result is False

    def test_mark_active_not_found(self, test_user):
        """Test marking non-existent session as active."""
        result = UserDeviceSessionService.mark_active("nonexistent")
        assert result is False
