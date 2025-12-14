from django.conf import settings
from django.db import models
from .recipe import Recipe


class Comment(models.Model):
    """User comments attached to recipes."""

    # Fields
    text = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    # Keys: link comments to recipes and users
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    def __str__(self):
        """Return the comment text as string representation."""
        return self.text

    class Meta:
        """Newest comments first."""

        ordering = ["-created_at"]