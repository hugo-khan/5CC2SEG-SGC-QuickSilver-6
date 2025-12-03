from django.conf import settings
from django.db import models
from django.utils import timezone


class Recipe(models.Model):
    """
    Unified Recipe model supporting:
    - legacy and new naming fields
    - tags
    - difficulty
    - dietary fields
    - optimized counter fields
    """

    DIETARY_CHOICES = [
        ("vegan", "Vegan"),
        ("vegetarian", "Vegetarian"),
        ("gluten_free", "Gluten Free"),
        ("dairy_free", "Dairy Free"),
        ("nut_free", "Nut Free"),
        ("none", "No Restrictions"),
    ]

    tags = models.ManyToManyField(
        "recipes.Tag",
        related_name="recipes",
        blank=True,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    # Core content fields
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=255, blank=True)
    ingredients = models.TextField(help_text="List ingredients separated by commas")
    instructions = models.TextField()

    name = models.CharField(max_length=255)
    description = models.TextField()

    # Image
    image = models.URLField(blank=True, null=True)

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

    # Dietary & popularity fields
    date_posted = models.DateTimeField(auto_now_add=True)
    dietary_requirement = models.CharField(
        max_length=50, choices=DIETARY_CHOICES, default="none"
    )
    popularity = models.IntegerField(default=0)

    # Counter fields (REQUIRED for optimized schema)
    likes_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-date_posted"]

    def __str__(self):
        return self.name or self.title

    @property
    def total_time_minutes(self):
        if self.cooking_time:
            return self.cooking_time
        prep = self.prep_time_minutes or 0
        cook = self.cook_time_minutes or 0
        return prep + cook

    @property
    def created_by(self):
        return self.author

    # Likes M2M through table
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_recipes",
        through="Like",
        blank=True,
    )
