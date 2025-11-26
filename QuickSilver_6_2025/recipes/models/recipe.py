from django.db import models
from django.conf import settings  

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    ingredients = models.TextField(help_text="List ingredients separated by commas")
    instructions = models.TextField(blank=True)
    cooking_time = models.PositiveIntegerField(help_text="Cooking time in minutes", default=0)
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='easy'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use this instead of 'auth.User'
        on_delete=models.CASCADE, 
        related_name='recipes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']