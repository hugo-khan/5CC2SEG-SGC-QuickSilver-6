from django.contrib import admin

from recipes.models import Follow, Recipe, User


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "is_published")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "summary", "author__username")
    autocomplete_fields = ("author",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
    search_fields = ("follower__username", "followed__username")
    autocomplete_fields = ("follower", "followed")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "first_name", "last_name")
    search_fields = ("username", "email", "first_name", "last_name")
