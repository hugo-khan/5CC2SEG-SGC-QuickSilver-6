from django.conf import settings
from django.db import models
from django.utils import timezone


class Recipe(models.Model):
    """
    A published recipe authored by a user.

    This model merges the original recipe fields (author, summary, prep/cook time,
    servings, publication flag) with the newer fields (cooking_time, difficulty)
    so that both sets of features work together.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    # Core content
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=255, blank=True)
    ingredients = models.TextField(help_text="List ingredients separated by commas")
    instructions = models.TextField()

    # Time & servings
    prep_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    cook_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    servings = models.PositiveSmallIntegerField(blank=True, null=True)

    # Publishing & difficulty
    is_published = models.BooleanField(default=True)
    cooking_time = models.PositiveIntegerField(
        help_text="Cooking time in minutes", default=0
    )
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
        ],
        default="easy",
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def total_time_minutes(self) -> int:
        """
        Total time in minutes, preferring the unified `cooking_time` field
        if it is set, otherwise falling back to prep + cook time.
        """
        if self.cooking_time:
            return self.cooking_time

        prep = self.prep_time_minutes or 0
        cook = self.cook_time_minutes or 0
        return prep + cook

    @property
    def created_by(self):
        """
        Backwards-compatible alias for code that expects `created_by`.
        """
        return self.author
