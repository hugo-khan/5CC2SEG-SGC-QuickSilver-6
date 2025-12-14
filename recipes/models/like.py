from django.db import models

from .recipe import Recipe
from .user import User


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
