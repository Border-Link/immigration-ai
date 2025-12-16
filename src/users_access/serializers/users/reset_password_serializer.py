from rest_framework import serializers
from .password_validation import PasswordValidation
from helpers import fields as input_fields
from users_access.services.user_service import UserService


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    retype_password = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def validate_new_password(self, new_password):
        email = self.initial_data.get(input_fields.EMAIL)
        return PasswordValidation(new_password, email).validate()

    def validate_retype_password(self, retype_password):
        if self.initial_data.get(input_fields.NEW_PASSWORD) != retype_password:
            raise serializers.ValidationError(input_fields.PASSWORD_DO_NOT_MATCH)
        return retype_password

    def validate_email(self, email):
        email = email.strip().lower()
        user = UserService().get_by_email(email)
        if not user:
            raise serializers.ValidationError(input_fields.EMAIL_DOES_NOT_EXIST)
        return user

