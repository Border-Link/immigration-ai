from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
import re

class PasswordValidation:

    def __init__(self, password: str, email: str):
        self.password = password
        self.email = email


    def validate(self):
        try:
            validate_password(self.password)
            if any(part.lower() in self.password.lower() for part in self.email.split('@')[0].split('.')):
                raise serializers.ValidationError("Password cannot be part of your email")
            if re.search(r'\d', self.password) is None:
                raise serializers.ValidationError("Password must contain a number")
            if re.search(r'[A-Z]', self.password) is None:
                raise serializers.ValidationError("Password must contain an uppercase")
            if re.search(r'[a-z]', self.password) is None:
                raise serializers.ValidationError("Password must contain a lowercase")
            if re.search(r'[!"#$%&()*+,-./:;<=>?@\^_`{|}~]\'', self.password) is None:
                raise serializers.ValidationError("Password must contain a special character")
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"password": e.detail})
        return self.password
