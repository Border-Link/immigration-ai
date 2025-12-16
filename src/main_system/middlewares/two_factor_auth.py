from django.conf import settings

class TwoFactorAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        path = request.path

        # Check if the user is authenticated and the 2FA is enabled
        if request.user.is_authenticated:
            enforce_path = getattr(settings, 'ENFORCE_2FA_PATHS', [])
            if any(path.startswith(p) for p in enforce_path):
                if not getattr(request.user.user_settings, 'two_factor_auth', False):
                    from rest_framework.response import Response
                    return Response(
                        {
                            "message": "Two-factor authentication is required."
                        },
                        status=403
                    )
        return self.get_response(request)