# recipes/services/image_service.py

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class ImageService:

    @staticmethod
    def compress_image(uploaded_file, max_width=1600, quality=80):
        """
        Compress and resize an uploaded image.
        
        - Converts to JPEG
        - Max width capped (keeps ratio)
        - Adjustable quality
        """

        # Open original image
        img = Image.open(uploaded_file)
        img = img.convert("RGB")  # ensures JPEG compatible

        # Resize if needed
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        # Return as Django ContentFile
        new_filename = uploaded_file.name.rsplit('.', 1)[0] + ".jpg"
        return ContentFile(buffer.read(), new_filename)
