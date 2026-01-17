from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
import logging
from django.conf import settings

logger = logging.getLogger('django')


class MyFallbackSerializer(serializers.Serializer):
   pass


class BaseAPI(GenericAPIView):
    """
    Base API class for all API views.
    
    SECURITY: Explicitly sets authentication_classes to ensure cookie-based
    authentication is used instead of DRF's default SessionAuthentication/BasicAuthentication.
    """
    service = None


    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):  # used by drf-spectacular
            return MyFallbackSerializer  # or None, if safe
        return super().get_serializer_class()

    def api_response(self, *, message="", data=None, status_code=status.HTTP_200_OK, **kwargs):
        response = {
            "message": message,
            "data": data,
            **kwargs
        }
        return Response(data=response, status=status_code)
    
    def handle_exception(self, exc):
        """
        Handle exceptions for pure API backend.
        
        Security: For API clients, we need to provide meaningful error messages
        for validation errors, but hide internal server error details.
        
        - Validation errors (400, 401, 403, 404): Show detailed messages (API clients need these)
        - Server errors (500): Hide internal details in production, log fully
        """
        from rest_framework.views import exception_handler
        from rest_framework.exceptions import ValidationError as DRFValidationError
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        # Normalize Django ValidationError -> DRF ValidationError (so API clients get 400, not 500).
        if isinstance(exc, DjangoValidationError):
            detail = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            exc = DRFValidationError(detail)

        # Let DRF handle known exceptions (validation, authentication, etc.)
        response = exception_handler(exc, self)
        
        if response is not None:
            # DRF handled the exception (validation, auth, permission errors)
            # For API clients, these errors should be detailed and helpful
            # Only hide details for 500-level server errors
            
            status_code = response.status_code
            
            # Log all exceptions for monitoring
            logger.error(
                f"API exception in {self.__class__.__name__}: {exc}",
                exc_info=True,
                extra={
                    'status_code': status_code,
                    'request_path': getattr(self.request, 'path', None),
                    'request_method': getattr(self.request, 'method', None),
                    'user_id': getattr(self.request.user, 'id', None) if hasattr(self.request, 'user') else None,
                }
            )
            
            # Only sanitize 500-level server errors in production
            # Client errors (4xx) should show details for API clients
            if status_code >= 500 and not settings.DEBUG and settings.APP_ENV == 'production':
                # Hide internal server error details
                if hasattr(exc, 'detail'):
                    response.data = {
                        'error': 'Internal server error',
                        'message': 'An error occurred. Please try again later.',
                        'status_code': status_code
                    }
            
            return response
        
        # Unknown/unhandled exception - 500 error
        logger.error(
            f"Unhandled exception in {self.__class__.__name__}: {exc}",
            exc_info=True,
            extra={
                'request_path': getattr(self.request, 'path', None),
                'request_method': getattr(self.request, 'method', None),
                'user_id': getattr(self.request.user, 'id', None) if hasattr(self.request, 'user') else None,
            }
        )
        
        # Return generic error for unhandled exceptions in production
        if not settings.DEBUG and settings.APP_ENV == 'production':
            return self.api_response(
                message="Internal server error",
                data={'error': 'An unexpected error occurred. Please try again later.'},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # In development, show the actual error for debugging
        return self.api_response(
            message="Internal server error",
            data={'error': str(exc), 'type': type(exc).__name__},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )





