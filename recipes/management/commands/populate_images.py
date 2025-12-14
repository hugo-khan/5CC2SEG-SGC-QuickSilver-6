"""Populate recipe images via Pexels; fallback to a black placeholder."""

import os
from io import BytesIO

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.text import slugify
from PIL import Image, ImageDraw

from recipes.models import Recipe


class Command(BaseCommand):
    help = "Populate recipe images using Pexels (food search) with fallback to local placeholder"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing images",
        )
        parser.add_argument(
            "--recipe-id",
            type=int,
            help="Only populate image for a specific recipe ID",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        recipe_id = options.get("recipe_id")

        # Get recipes to process
        if recipe_id:
            recipes = Recipe.objects.filter(pk=recipe_id)
            if not recipes.exists():
                self.stdout.write(
                    self.style.ERROR(f"Recipe with ID {recipe_id} not found")
                )
                return
        else:
            if overwrite:
                recipes = Recipe.objects.all()
            else:
                recipes = Recipe.objects.filter(
                    models.Q(image__isnull=True) | models.Q(image="")
                )

        total = recipes.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No recipes to process"))
            return

        self.stdout.write(f"Processing {total} recipe(s) using Pexels...")

        success_count = 0
        error_count = 0

        for recipe in recipes:
            try:
                image_url = self.get_pexels_image(recipe)

                basename = slugify(recipe.title) or f"recipe-{recipe.id}"
                image_file = self.download_image_to_file(image_url, basename)

                if not image_file:
                    image_file = self.generate_placeholder_image(recipe.title, basename)

                if image_file:
                    filename = f"{basename}.jpg"
                    recipe.image.save(filename, image_file, save=False)
                    recipe.image_url = image_url
                    recipe.save(update_fields=["image", "image_url"])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Added image to "{recipe.title}" (ID: {recipe.id})'
                        )
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Could not get image for "{recipe.title}" (ID: {recipe.id})'
                        )
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error processing "{recipe.title}" (ID: {recipe.id}): {str(e)}'
                    )
                )
                error_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed: {success_count} successful, {error_count} errors"
            )
        )

    def get_pexels_image(self, recipe):
        """Fetch a food image URL from Pexels or return None."""
        api_key = os.environ.get("PEXELS_API_KEY")
        if not api_key:
            self.stdout.write(
                self.style.WARNING("PEXELS_API_KEY not set; using placeholders.")
            )
            return None

        if not self._looks_like_food(recipe):
            return None

        query = recipe.title or "food"
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": api_key},
                params={
                    "query": query,
                    "per_page": 1,
                    "orientation": "landscape",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                self.stdout.write(
                    self.style.WARNING(
                        f"Pexels API returned {resp.status_code} for '{query}'"
                    )
                )
                return None
            data = resp.json()
            photos = data.get("photos") or []
            if not photos:
                return None
            src = photos[0].get("src") or {}
            # Prefer large landscape variants; fallback to original
            return src.get("large2x") or src.get("large") or src.get("original")
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(f"Pexels fetch failed for '{query}': {exc}")
            )
            return None

    def download_image_to_file(self, url, basename):
        """Download an image and return it as ContentFile or None."""
        if not url:
            return None

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            # Validate image by attempting to open it
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=80, optimize=True)
            buffer.seek(0)
            return ContentFile(buffer.read(), name=f"{basename}.jpg")
        except Exception:
            return None

    def generate_placeholder_image(self, title, basename):
        """Create a black gradient placeholder image."""
        width, height = 1200, 800
        base_color = (10, 10, 10)
        accent_color = (0, 0, 0)

        img = Image.new("RGB", (width, height), color=base_color)
        draw = ImageDraw.Draw(img)

        # Subtle vertical gradient
        for y in range(height):
            blend = y / height
            r = int(base_color[0] * (1 - blend) + accent_color[0] * blend)
            g = int(base_color[1] * (1 - blend) + accent_color[1] * blend)
            b = int(base_color[2] * (1 - blend) + accent_color[2] * blend)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        return ContentFile(buffer.read(), name=f"{basename}.jpg")

    def _looks_like_food(self, recipe):
        """Heuristic: True if ingredients or title look food-related."""
        if recipe.ingredients:
            # If there are commas or multiple words, assume it's food
            if "," in recipe.ingredients or len(recipe.ingredients.split()) > 3:
                return True

        food_words = [
            "chicken",
            "beef",
            "pasta",
            "salad",
            "soup",
            "curry",
            "cookie",
            "cake",
            "taco",
            "noodle",
            "pizza",
            "burger",
            "fish",
            "vegetable",
            "veggie",
            "rice",
            "stir",
            "fry",
        ]
        title_lower = (recipe.title or "").lower()
        return any(word in title_lower for word in food_words)
