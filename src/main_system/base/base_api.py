from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers


class MyFallbackSerializer(serializers.Serializer):
   pass


class BaseAPI(GenericAPIView):
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





