from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .cookies_access.local_device_access_manager import LocalDeviceSessionRefreshMiddleware
from .cookies_access.production_device_access_manager import ProductionDeviceSessionRefreshMiddleware
import logging

logger = logging.getLogger('django')


APP_ENVIRONMENTS = ["local", "dev"]

REQUEST_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

class DeviceSessionRefreshMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if settings.APP_ENV in APP_ENVIRONMENTS:
            return LocalDeviceSessionRefreshMiddleware().process_request(request=request)
        return ProductionDeviceSessionRefreshMiddleware().process_request(request=request)

    def process_response(self, request, response):
        if settings.APP_ENV in APP_ENVIRONMENTS:
            return LocalDeviceSessionRefreshMiddleware().process_response(request=request, response=response)
        return ProductionDeviceSessionRefreshMiddleware().process_response(request=request, response=response)
