from .base_cookies_access import BaseCookieAccessTokenAuthentication
class LocalCookieAccessTokenAuthentication:

    def authenticate(self, request):
        return BaseCookieAccessTokenAuthentication.validate_token_and_device(request, require_session=False)