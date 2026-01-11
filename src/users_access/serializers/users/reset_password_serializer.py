from rest_framework import serializers
from .password_validation import PasswordValidation
from users_access.services.user_service import UserService


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    retype_password = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def validate_new_password(self, new_password):
        email = self.initial_data.get("email")
        return PasswordValidation(new_password, email).validate()

    def validate_retype_password(self, retype_password):
        if self.initial_data.get("new_password") != retype_password:
            raise serializers.ValidationError("Passwords do not match")
        return retype_password

    def validate_email(self, email):
        email = email.strip().lower()
        user = UserService().get_by_email(email)
        if not user:
            raise serializers.ValidationError("Email does not exist")
        return user

