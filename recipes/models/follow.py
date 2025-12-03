from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Follow(models.Model):
    """Represents a follower relationship between two users."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="following",
        on_delete=models.CASCADE,
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="followers",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("follower", "followed"),
                name="unique_follow_relationship",
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("followed")),
                name="prevent_self_follow",
            ),
        ]
        ordering = ["-created_at"]

    def clean(self):
        if self.follower == self.followed:
            raise ValidationError("Users cannot follow themselves.")

    def __str__(self):
        return f"{self.follower} follows {self.followed}"


