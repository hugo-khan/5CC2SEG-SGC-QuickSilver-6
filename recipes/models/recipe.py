import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from recipes.image_service import ImageService  


class Recipe(models.Model):
    """Unified recipe model keeping legacy and new fields."""

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
    summary = models.CharField(max_length=255, blank=True, default="")
    ingredients = models.TextField(help_text="List ingredients separated by commas", blank=True, default="")
    instructions = models.TextField(blank=True, default="")

    name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")

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
    # Allow fixtures or auto timestamp
    date_posted = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    dietary_requirement = models.CharField(
        max_length=50, choices=DIETARY_CHOICES, default="none"
    )
    popularity = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True, blank=True)
    # Allow null/default for legacy fixtures; updated on save.
    updated_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    # Sharing
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Seeded image
    image_url = models.URLField(blank=True, null=True, help_text="External image URL")


    # Main recipe image (uploaded file, compressed on save)
    image = models.ImageField(
        upload_to="recipes/",
        blank=True,
        null=True,
        help_text="Main image for this recipe",
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

    class Meta:
        ordering = ["-created_at", "-date_posted"]

    def __str__(self) -> str:
        """Prefer name over title when available."""
        return self.name or self.title

    def save(self, *args, **kwargs):
        """Compress new images, bump updated_at, and drop replaced images."""

        # Capture old image before potential replacement
        old_image = None
        if self.pk:
            try:
                old_image = Recipe.objects.get(pk=self.pk).image
            except Recipe.DoesNotExist:
                pass

        # Always bump updated_at
        self.updated_at = timezone.now()

        # Compress uploaded image before saving
        if self.image and hasattr(self.image, "file"):
            self.image = ImageService.compress_image(self.image)

        super().save(*args, **kwargs)

        # Delete the previous image file if it changed
        if old_image and old_image != self.image:
            old_image.delete(save=False)

    @property
    def total_time_minutes(self) -> int:
        """Return total time preferring cooking_time else prep + cook."""
        if self.cooking_time:
            return self.cooking_time

        prep = self.prep_time_minutes or 0
        cook = self.cook_time_minutes or 0
        return prep + cook

    @property
    def created_by(self):
        """Backwards-compatible alias for code expecting created_by."""
        return self.author

    def get_share_url(self, request):
        """Generate a shareable URL for this recipe."""
        from django.urls import reverse
        return request.build_absolute_uri(
            reverse('recipe_share', kwargs={'share_token': self.share_token})
        )


