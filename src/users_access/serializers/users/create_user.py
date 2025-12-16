from rest_framework import serializers
from .password_validation import PasswordValidation
from helpers import fields as input_fields
from users_access.models.user import User
from users_access.services.user_service import UserService


class CreateUserSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=True, max_length=255)
    last_name = serializers.CharField(required=True, max_length=255)

    class Meta:
        model = User
        fields = (input_fields.EMAIL, input_fields.PASSWORD, input_fields.FIRST_NAME, input_fields.LAST_NAME)
        extra_kwargs = {
            input_fields.PASSWORD:{input_fields.WRITE_ONLY: True}
        }


    def validate_email(self, value):
        email = value.strip().lower()
        if UserService().email_exists(email):
            raise serializers.ValidationError(input_fields.EMAIL_ALREADY_EXISTS)
        return email


    def validate_password(self, password):
        email = self.initial_data.get(input_fields.EMAIL, input_fields.EMPTY_STRING).strip().lower()
        return PasswordValidation(password, email).validate()
