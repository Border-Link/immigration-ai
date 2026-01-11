from rest_framework import serializers
from main_system.utils import image_processor as img_processor

class UserAvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(required=True)

    def validate_avatar(self, value):
       target_size_kb = 500
       image_quality = 85
       image_format = "WEBP"
       return img_processor.ImageProcessor(value, target_size_kb, image_quality, image_format).process()


