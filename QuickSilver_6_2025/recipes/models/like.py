from django.db import models
from .user import user
from .recipe import recipe

class Like(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name ='likes')
    recipe = models.ForeignKey(recipe, on_delete=models.CASCADE, related_name ='likes')

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user} likes {self.recipe}'