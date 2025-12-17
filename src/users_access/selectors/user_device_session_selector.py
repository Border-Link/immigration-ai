from users_access.models import UserDeviceSession


class UserDeviceSessionSelector:

    @staticmethod
    def active_sessions_for_user(user):
        return UserDeviceSession.objects.filter(
            user=user, revoked=False, revoked_at__isnull=True
        ).order_by("-last_active")

    @staticmethod
    def get_by_session_id(session_id, fingerprint=None):
        qs = UserDeviceSession.objects.filter(
            session_id=session_id, revoked=False, revoked_at__isnull=True
        )
        if fingerprint:
            qs = qs.filter(fingerprint=fingerprint)
        return qs.first()
