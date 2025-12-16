from typing import Optional
from rest_framework import serializers
from helpers import fields as input_fields

class NamesUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=255)
    last_name = serializers.CharField(required=True, max_length=255)

    def validate_first_name(self, first_name: Optional[str]):
        first_name = first_name.strip()
        if not first_name:
            raise serializers.ValidationError(input_fields.FIRST_NAME_IS_REQUIRED)
        return first_name


    def validate_last_name(self, last_name: Optional[str]):
        last_name = last_name.strip()
        if not last_name:
            raise serializers.ValidationError(input_fields.LAST_NAME_IS_REQUIRED)
        return last_name
