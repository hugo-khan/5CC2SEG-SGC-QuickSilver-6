import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Recipe(models.Model):
    """
    Unified Recipe model that keeps all fields from both branches so that:
    - original timing/difficulty/publishing fields continue to work
    - newer dietary/popularity fields are also available
    - both naming schemes (`title`/`summary` and `name`/`description`) coexist
    """

    DIETARY_CHOICES = [
        ("vegan", "Vegan"),
        ("vegetarian", "Vegetarian"),
        ("gluten_free", "Gluten Free"),
        ("dairy_free", "Dairy Free"),
        ("nut_free", "Nut Free"),
        ("none", "No Restrictions"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    # Core content (keep both naming conventions)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=255, blank=True)
    ingredients = models.TextField(help_text="List ingredients separated by commas")
    instructions = models.TextField()

    name = models.CharField(max_length=255)
    description = models.TextField()

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

    # Newer dietary/popularity fields
    date_posted = models.DateTimeField(auto_now_add=True)
    dietary_requirement = models.CharField(
        max_length=50, choices=DIETARY_CHOICES, default="none"
    )
    popularity = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    # Sharing
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Image - Using URLField only to avoid Pillow dependency issues
    # Can add ImageField later if needed after installing system dependencies
    image_url = models.URLField(blank=True, null=True, help_text="External image URL (e.g., from AI generation or Unsplash)")

    class Meta:
        ordering = ["-created_at", "-date_posted"]

    def __str__(self) -> str:
        """
        Prefer the newer `name` field for consistency with the newer admin/views,
        but fall back to `title` if needed.
        """
        return self.name or self.title

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

    def get_share_url(self, request):
        """
        Generate a shareable URL for this recipe.
        """
        from django.urls import reverse
        return request.build_absolute_uri(
            reverse('recipe_share', kwargs={'share_token': self.share_token})
        )

    # Users who liked this recipe.
    # We keep the ManyToMany interface expected by the like feature/tests,
    # but route it through the dedicated Like model so we don't lose any
    # information or constraints.
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_recipes",
        through="Like",
        blank=True,
    )
