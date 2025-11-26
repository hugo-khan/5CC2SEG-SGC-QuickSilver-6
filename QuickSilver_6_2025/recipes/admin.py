from django.contrib import admin
from recipes.models import Recipe

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'author', 'dietary_requirement', 'popularity', 'date_posted']
    list_filter = ['dietary_requirement', 'date_posted', 'popularity']
    search_fields = ['name', 'description', 'author__username']
    readonly_fields = ['date_posted']