from django.conf import settings
from django.db import models
from django.utils import timezone


class Recipe(models.Model):
    """A published recipe authored by a user."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=255, blank=True)
    ingredients = models.TextField()
    instructions = models.TextField()
    prep_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    cook_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    servings = models.PositiveSmallIntegerField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_time_minutes(self):
        prep = self.prep_time_minutes or 0
        cook = self.cook_time_minutes or 0
        return prep + cook


