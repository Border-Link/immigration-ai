from .base_cookies_access import BaseCookieAccessTokenAuthentication

class ProductionCookieAccessTokenAuthentication:

    def authenticate(self, request):
        return BaseCookieAccessTokenAuthentication.validate_token_and_device(request, require_session=True)