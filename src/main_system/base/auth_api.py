from .base_api import BaseAPI
from django_filters.rest_framework import DjangoFilterBackend
from ..middlewares.cookie_access_only import CookieAccessOnlyTokenAuthentication


class AuthAPI(BaseAPI):
    authentication_classes = [CookieAccessOnlyTokenAuthentication]
    filter_backends = [DjangoFilterBackend]



