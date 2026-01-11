from io import BytesIO
from PIL import Image, UnidentifiedImageError
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers

class ImageProcessor:

    def __init__(self, image, target_size_kb=500, image_quality=85, image_format= "WEBP"):
        self.image = image
        self.target_size_kb = target_size_kb
        self.image_quality = image_quality
        self.image_format = image_format


    def process(self):
        image  = self.image

        try:
            img = Image.open(image)
            img.verify()
        except UnidentifiedImageError:
            raise serializers.ValidationError("Uploaded file is not a valid image.")

        image.file.seek(0)
        img = Image.open(image)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        img = self._dynamic_resize(img)

        output_io = BytesIO()
        img.save(output_io, format=self.image_format, quality=self.image_quality)

        new_img = self._optimize_file_size(img, output_io)

        return InMemoryUploadedFile(
            file=new_img,
            field_name=image.field_name,
            name=f"{image.name.split('.')[0]}.webp",
            content_type=f"image/{self.image_format.lower().strip()}",
            size=new_img.tell(),
            charset=None
        )


    def _dynamic_resize(self, img):
        max_dimension = 1024
        width, height = img.size

        if max(width, height) > max_dimension:
            scaling_factor = max_dimension / float(max(width, height))
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)
            img = img.resize((new_width, new_height), Image.LANCZOS)

        return img


    def _optimize_file_size(self, img, output_io):
        for quality in range(self.image_quality, 50, -5):
            output_io = BytesIO()
            img.save(output_io, format=self.image_format, quality=quality)
            if output_io.tell() / 1024 <= self.target_size_kb:
                break

        return output_io


