"""
Management command to populate recipe images using AI-generated or food photography.
Uses Unsplash Source API (free, no key needed) for food images based on recipe titles.
Can be extended to use OpenAI DALL-E or other AI services.
"""

import os
import requests
from django.core.management.base import BaseCommand
from recipes.models import Recipe


class Command(BaseCommand):
    help = 'Populate recipe images using AI-generated or food photography'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            default='unsplash',
            choices=['unsplash', 'placeholder'],
            help='Method to use for image generation (default: unsplash)',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing images',
        )
        parser.add_argument(
            '--recipe-id',
            type=int,
            help='Only populate image for a specific recipe ID',
        )

    def handle(self, *args, **options):
        method = options['method']
        overwrite = options['overwrite']
        recipe_id = options.get('recipe_id')

        # Get recipes to process
        if recipe_id:
            recipes = Recipe.objects.filter(pk=recipe_id)
            if not recipes.exists():
                self.stdout.write(
                    self.style.ERROR(f'Recipe with ID {recipe_id} not found')
                )
                return
        else:
            if overwrite:
                recipes = Recipe.objects.all()
            else:
                recipes = Recipe.objects.filter(image_url__isnull=True)

        total = recipes.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No recipes to process'))
            return

        self.stdout.write(f'Processing {total} recipe(s) using {method} method...')

        success_count = 0
        error_count = 0

        for recipe in recipes:
            try:
                if method == 'unsplash':
                    image_url = self.get_unsplash_image(recipe)
                elif method == 'placeholder':
                    image_url = self.get_placeholder_image(recipe)
                else:
                    image_url = None

                if image_url:
                    # Save URL to model (no need to download since we're using external URLs)
                    recipe.image_url = image_url
                    recipe.save()

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

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed: {success_count} successful, {error_count} errors'
            )
        )

    def get_unsplash_image(self, recipe):
        """
        Get a food image from Unsplash Source API based on recipe title.
        Unsplash Source API is free and doesn't require an API key.
        """
        # Clean up recipe title for search
        search_term = recipe.title.lower()
        
        # Remove common words that don't help with image search
        stop_words = ['recipe', 'how to', 'easy', 'quick', 'best', 'classic', 'homemade']
        for word in stop_words:
            search_term = search_term.replace(word, '')
        
        search_term = search_term.strip().replace(' ', '-')
        
        # Use Unsplash Source API (free, no key needed)
        # Format: https://source.unsplash.com/800x600/?{search-term}
        # We'll use food-related keywords
        image_url = f'https://source.unsplash.com/800x600/?food,{search_term}'
        
        # Try to verify the image exists
        try:
            response = requests.head(image_url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                return image_url
        except:
            pass
        
        # Fallback to generic food image
        return 'https://source.unsplash.com/800x600/?food,cuisine'

    def get_placeholder_image(self, recipe):
        """
        Get a placeholder image service URL.
        This is a fallback option.
        """
        # Using placeholder.com or similar service
        search_term = recipe.title.replace(' ', '%20')
        return f'https://via.placeholder.com/800x600/cccccc/666666?text={search_term}'

