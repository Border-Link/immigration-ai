from users_access.repositories.user_device_session_repository import UserDeviceSessionRepository
from users_access.selectors.user_device_session_selector import UserDeviceSessionSelector
import logging

logger = logging.getLogger("django")


class UserDeviceSessionService:

    @staticmethod
    def create_device_session(user, fingerprint, ip_address, user_agent, device_info, session_id, last_active):
        try:
            return UserDeviceSessionRepository.create_device_session(
                user, fingerprint, ip_address, user_agent, device_info, session_id, last_active
            )
        except Exception as e:
            logger.exception(f"Error creating device session for user {user.id}: {e}")
            return None

    @staticmethod
    def active_sessions_for_user(user):
        try:
            return UserDeviceSessionSelector.active_sessions_for_user(user)
        except Exception as e:
            logger.exception(f"Error fetching active sessions for user {user.id}: {e}")
            return []

    @staticmethod
    def get_by_session_id(session_id, fingerprint=None):
        try:
            return UserDeviceSessionSelector.get_by_session_id(session_id, fingerprint)
        except Exception as e:
            logger.exception(f"Error fetching session {session_id}: {e}")
            return None

    @staticmethod
    def revoke_session(session_id):
        try:
            session = UserDeviceSessionSelector.get_by_session_id(session_id)
            if not session:
                return False
            return UserDeviceSessionRepository.revoke_session(session)
        except Exception as e:
            logger.exception(f"Error revoking session {session_id}: {e}")
            return False

    @staticmethod
    def revoke_all_for_user(user):
        try:
            return UserDeviceSessionRepository.revoke_all_for_user(user)
        except Exception as e:
            logger.exception(f"Error revoking all sessions for user {user.id}: {e}")
            return False

    @staticmethod
    def mark_active(session_id):
        try:
            session = UserDeviceSessionSelector.get_by_session_id(session_id)
            if not session:
                return False
            return UserDeviceSessionRepository.mark_active(session)
        except Exception as e:
            logger.exception(f"Error marking session {session_id} active: {e}")
            return False
