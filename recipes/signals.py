# recipes/signals.py

import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from recipes.models import Recipe

def delete_recipe_image(image_field):
    """Delete a FileField/ImageField if it exists."""
    if image_field and hasattr(image_field, "path"):
        image_field.delete(save=False)


@receiver(post_delete, sender=Recipe)
def delete_image_on_recipe_delete(sender, instance, **kwargs):
    """Delete image file when recipe is deleted."""
    delete_recipe_image(instance.image)


@receiver(pre_save, sender=Recipe)
def delete_old_image_on_change(sender, instance, **kwargs):
    """
    Delete old image file when:
    - user uploads a new image
    - user clears the existing image
    """
    if not instance.pk:
        # Creating a new recipe → nothing to delete
        return

    try:
        old = Recipe.objects.get(pk=instance.pk)
    except Recipe.DoesNotExist:
        return

    old_image = old.image
    new_image = instance.image

    # If image changed (new upload OR cleared), delete old file
    if old_image and old_image != new_image:
        delete_recipe_image(old_image)

