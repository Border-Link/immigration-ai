from rest_framework import serializers
from users_access.services.user_service import UserService


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        email = email.strip().lower()
        user = UserService().get_by_email(email)
        if not user:
            raise serializers.ValidationError("Email does not exist")

        return user