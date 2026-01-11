from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from .password_validation import PasswordValidation


class PasswordUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)
    old_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not check_password(value, user.password):
            raise serializers.ValidationError("Invalid old password")


    def validate_password(self, password):
        email = self.instance.email
        return PasswordValidation(password, email).validate()

