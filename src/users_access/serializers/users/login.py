from rest_framework import serializers
from users_access.services.user_service import UserService


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get("email").lower()
        password = attrs.get("password")
        if not email or not password:
            raise serializers.ValidationError("Email and password is required")

        if not UserService().email_exists(email):
            raise serializers.ValidationError("Invalid credentials entered.")

        user, error = UserService.login(email=email, password=password, request=self.context.get("request"))
        if error:
            raise serializers.ValidationError(error)

        attrs["user"] = user
        return attrs


class TwoFactorVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6)
    is_2fa = serializers.BooleanField(default=False)


