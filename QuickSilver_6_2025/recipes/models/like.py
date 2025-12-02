from django.db import models

from .user import User
from .recipe import Recipe


class Like(models.Model):
    """Explicit like relationship between a user and a recipe."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="like_relations",
    )

    class Meta:
        unique_together = ("user", "recipe")

    def __str__(self) -> str:
        return f"{self.user} likes {self.recipe}"