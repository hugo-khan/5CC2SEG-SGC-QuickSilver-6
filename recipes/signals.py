# recipes/signals.py

import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from recipes.models import Recipe


def delete_recipe_image(recipe):
    """Utility that deletes the recipe image file if it exists."""
    if recipe.image:
        recipe.image.delete(save=False)


@receiver(post_delete, sender=Recipe)
def delete_image_on_recipe_delete(sender, instance, **kwargs):
    delete_recipe_image(instance)
