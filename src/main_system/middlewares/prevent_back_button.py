from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger('django')


class PreventBackButtonMiddleware(MiddlewareMixin):
    """
    Prevents browser caching and enforces security headers including
    CSP based on CORS_ALLOWED_ORIGINS.
    """

    def process_response(self, request, response):
        try:
            # Prevent caching for authenticated users
            if request.user.is_authenticated:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

            # Security headers
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # SECURITY: Removed CSP from this middleware to avoid conflicts
            # CSP is now handled by SecurityHeadersMiddleware with strict policies
            # This prevents unsafe-inline/unsafe-eval vulnerabilities
            # Only set basic security headers here, CSP is handled elsewhere

        except Exception as e:
            logger.warning(f"PreventBackButtonMiddleware error: {e}")

        return response
