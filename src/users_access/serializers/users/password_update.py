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
        return value


    def validate_password(self, password):
        email = getattr(self.context.get("request"), "user", None)
        email = getattr(email, "email", "") or ""
        return PasswordValidation(password, email).validate()

