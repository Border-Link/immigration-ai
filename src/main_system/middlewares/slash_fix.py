from django.conf import settings
from django.http import JsonResponse

class EnforceTrailingSlashMiddleware:
    """
    Middleware that checks if a POST request URL ends with a slash.
    If not, returns a 400 Bad Request JSON error telling the client to add a trailing slash.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.APPEND_SLASH
            and not request.path.endswith('/')
            and not request.path_info.endswith('/')
        ):
            return JsonResponse(
                {
                    "detail": "request URLs must end with a trailing slash ('/'). Please update your request URL."
                },
                status=400,
            )
        return self.get_response(request)
