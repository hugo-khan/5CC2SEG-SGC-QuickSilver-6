import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Recipe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                # Original textual and timing fields
                ("title", models.CharField(max_length=200)),
                ("summary", models.CharField(blank=True, max_length=255)),
                (
                    "ingredients",
                    models.TextField(help_text="List ingredients separated by commas"),
                ),
                ("instructions", models.TextField()),
                (
                    "prep_time_minutes",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "cook_time_minutes",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("servings", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("is_published", models.BooleanField(default=True)),
                (
                    "cooking_time",
                    models.PositiveIntegerField(
                        default=0, help_text="Cooking time in minutes"
                    ),
                ),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("easy", "Easy"),
                            ("medium", "Medium"),
                            ("hard", "Hard"),
                        ],
                        default="easy",
                        max_length=10,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                # Newer naming/date/dietary/popularity fields
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("date_posted", models.DateTimeField(auto_now_add=True)),
                (
                    "dietary_requirement",
                    models.CharField(
                        choices=[
                            ("vegan", "Vegan"),
                            ("vegetarian", "Vegetarian"),
                            ("gluten_free", "Gluten Free"),
                            ("dairy_free", "Dairy Free"),
                            ("nut_free", "Nut Free"),
                            ("none", "No Restrictions"),
                        ],
                        default="none",
                        max_length=50,
                    ),
                ),
                ("popularity", models.IntegerField(default=0)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recipes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                # Keep original ordering plus a secondary ordering on the newer field
                "ordering": ["-created_at", "-date_posted"],
            },
        ),
    ]
