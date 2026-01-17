from django.conf import settings
from knox.auth import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
import logging
from .cookies_access.local_cookie_access import LocalCookieAccessTokenAuthentication
from .cookies_access.production_cookie_access import ProductionCookieAccessTokenAuthentication

logger = logging.getLogger('django')
APP_ENVIRONMENTS = ["local", "dev"]

class CookieAccessOnlyTokenAuthentication(TokenAuthentication):
    """
    Cookie-based token authentication.
    
    Reads access token, session ID, and fingerprint from cookies.
    Validates the token and device session before authenticating the user.
    """

    def authenticate(self, request):
        """
        Authenticate user from cookies.
        
        This method is called by DRF's perform_authentication() during
        the initial() phase, BEFORE permission checks.
        """
        
        try:
            if settings.APP_ENV in APP_ENVIRONMENTS:
                result = LocalCookieAccessTokenAuthentication().authenticate(request=request)
            else:
                result = ProductionCookieAccessTokenAuthentication().authenticate(request=request)
            if result is None:
                return None
            
            if result and len(result) == 2:
                user, token = result
                return user, token

            return None
            
        except AuthenticationFailed as e:
            raise
        except Exception as e:
            raise AuthenticationFailed(f"Authentication failed: {str(e)}")