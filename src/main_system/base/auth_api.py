from rest_framework.permissions import IsAuthenticated
from .base_api import BaseAPI
from django_filters.rest_framework import DjangoFilterBackend


class AuthAPI(BaseAPI):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]



