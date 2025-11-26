from django.db import models
from django.conf import settings

class Recipe(models.Model):
    DIETARY_CHOICES = [
        ('vegan', 'Vegan'),
        ('vegetarian', 'Vegetarian'),
        ('gluten_free', 'Gluten Free'),
        ('dairy_free', 'Dairy Free'),
        ('nut_free', 'Nut Free'),
        ('none', 'No Restrictions'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    date_posted = models.DateTimeField(auto_now_add=True)
    dietary_requirement = models.CharField(max_length=50, choices=DIETARY_CHOICES, default='none')
    popularity = models.IntegerField(default=0)  # Number of views/likes
    
    class Meta:
        ordering = ['-date_posted']
    
    def __str__(self):
        return self.name