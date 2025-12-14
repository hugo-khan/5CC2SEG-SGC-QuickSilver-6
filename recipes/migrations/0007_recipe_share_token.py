# Generated migration for recipe sharing feature

import uuid

from django.db import migrations, models


def generate_share_tokens(apps, schema_editor):
    """Generate unique share tokens for all existing recipes."""
    Recipe = apps.get_model("recipes", "Recipe")
    for recipe in Recipe.objects.all():
        recipe.share_token = uuid.uuid4()
        recipe.save(update_fields=["share_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0006_comment_like_recipe_likes"),
    ]

    operations = [
        # First, add the field as nullable and non-unique
        migrations.AddField(
            model_name="recipe",
            name="share_token",
            field=models.UUIDField(null=True, editable=False, unique=False),
        ),
        # Generate unique tokens for all existing recipes
        migrations.RunPython(generate_share_tokens, migrations.RunPython.noop),
        # Now make it non-nullable and unique
        migrations.AlterField(
            model_name="recipe",
            name="share_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
