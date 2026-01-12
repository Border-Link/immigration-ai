"""
Security Headers Middleware for API-only Django backends.

Adds important security headers to HTTP responses for better protection.
"""

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add essential security headers for API responses.
    """

    def process_response(self, request, response):
        """
        Add security headers to the response.
        """

        # HSTS (Strict-Transport-Security) - only in production
        if getattr(settings, "APP_ENV", "") == "production":
            if not response.has_header("Strict-Transport-Security"):
                response["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )

        # Prevent MIME type sniffing
        if not response.has_header("X-Content-Type-Options"):
            response["X-Content-Type-Options"] = "nosniff"

        # Referrer Policy
        if not response.has_header("Referrer-Policy"):
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
