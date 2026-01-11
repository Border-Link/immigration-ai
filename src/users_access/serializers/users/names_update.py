from typing import Optional
from rest_framework import serializers


class NamesUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=255)
    last_name = serializers.CharField(required=True, max_length=255)

    def validate_first_name(self, first_name: Optional[str]):
        first_name = first_name.strip()
        if not first_name:
            raise serializers.ValidationError("First name is required.")
        return first_name


    def validate_last_name(self, last_name: Optional[str]):
        last_name = last_name.strip()
        if not last_name:
            raise serializers.ValidationError("Last name is required.")
        return last_name
