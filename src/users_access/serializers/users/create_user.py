from rest_framework import serializers
from .password_validation import PasswordValidation
from users_access.models.user import User
from users_access.services.user_service import UserService


class CreateUserSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=True, max_length=255)
    last_name = serializers.CharField(required=True, max_length=255)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")
        extra_kwargs = {
            "password": {"write_only": True}
        }


    def validate_email(self, value):
        email = value.strip().lower()
        if UserService().email_exists(email):
            raise serializers.ValidationError("Email already exists")
        return email


    def validate_password(self, password):
        email = self.initial_data.get("email", "").strip().lower()
        return PasswordValidation(password, email).validate()
