from django.contrib import admin
from recipes.models import Follow, Recipe, User, CommentReport, Comment


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Admin for Recipe that exposes both the original timing/difficulty fields
    and the newer dietary/popularity fields so all features remain usable.
    """

    # Combine fields from both versions of Recipe
    list_display = (
        "title",  # original
        "author",
        "dietary_requirement",  # newer
        "popularity",  # newer
        "created_at",  # original timestamp
        "is_published",  # original
    )
    list_filter = (
        "dietary_requirement",
        "created_at",
        "popularity",
        "is_published",
        "difficulty",
    )
    search_fields = (
        "title",
        "summary",
        "description",
        "author__username",
    )
    readonly_fields = ("date_posted", "created_at", "updated_at")
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

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'created_at')
    search_fields = ('text','user__username')
    ordering = ('created_at',)

@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ('id','comment', 'created_at','reporter') # for the comments
    search_fields = ('reporter__username', 'reason', 'comment__text')
    ordering = ('created_at',)

