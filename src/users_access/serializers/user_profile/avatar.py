from rest_framework import serializers
from users_access.serializers.users import add_avatar

class UserAvatarSerializer(serializers.Serializer):
    # Use FileField (not ImageField) so we can validate via ImageProcessor,
    # and keep tests flexible when they pass mock files.
    avatar = serializers.FileField(required=True)

    def validate_avatar(self, value):
       target_size_kb = 500
       image_quality = 85
       image_format = "WEBP"
       return add_avatar.img_processor.ImageProcessor(value, target_size_kb, image_quality, image_format).process()
