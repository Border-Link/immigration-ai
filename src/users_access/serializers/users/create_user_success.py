from rest_framework import serializers
from users_access.models.user import User
from helpers import fields as input_fields

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            input_fields.ID,
            input_fields.EMAIL,
            input_fields.FIRST_NAME,
            input_fields.LAST_NAME,
            input_fields.IS_ACTIVE,
            input_fields.IS_SUPERUSER,
            input_fields.IS_STAFF,
            input_fields.CREATED_AT,
            input_fields.UPDATED_AT,
        )

        read_only_fields = (
            input_fields.ID,
            input_fields.IS_ACTIVE,
            input_fields.IS_SUPERUSER,
            input_fields.IS_STAFF,
            input_fields.CREATED_AT,
            input_fields.UPDATED_AT,
        )
class WhoAmISerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            input_fields.ID,
            input_fields.EMAIL,
            input_fields.FIRST_NAME,
            input_fields.LAST_NAME,
            input_fields.IS_ACTIVE,
        )