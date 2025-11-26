from django.db import models
from django.conf import settings
from .recipe import recipe

class Comment(models.Model):

    #fields
    text = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    #keys, link a comments to recipes and user to their comments
    recipe = models.ForeignKey(recipe, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    #put newest comments first
    class Meta:
        ordering = ["-created_at"]