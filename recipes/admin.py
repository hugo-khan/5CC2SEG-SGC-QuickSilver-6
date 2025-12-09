from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from recipes.models import Follow, Recipe, User


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Admin for Recipe that exposes both the original timing/difficulty fields
    and the newer dietary/popularity fields so all features remain usable.
    
    Admins can delete any recipe through this interface.
    """

    # Combine fields from both versions of Recipe
    list_display = (
        "title",  # original
        "author",
        "dietary_requirement",  # newer
        "popularity",  # newer
        "created_at",  # original timestamp
        "is_published",  # original
        "view_recipe_link",  # Link to view recipe
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
    readonly_fields = ("date_posted", "created_at", "updated_at", "view_recipe_link")
    autocomplete_fields = ("author",)
    
    # Enable deletion in admin (default is True, but making it explicit)
    def has_delete_permission(self, request, obj=None):
        """Allow admins to delete any recipe."""
        return request.user.is_staff
    
    def view_recipe_link(self, obj):
        """Add a link to view the recipe on the site."""
        if obj.pk:
            url = reverse('recipe_detail', kwargs={'pk': obj.pk})
            return format_html('<a href="{}" target="_blank">View Recipe</a>', url)
        return "-"
    view_recipe_link.short_description = "View on Site"
    
    # Admin actions for bulk operations
    actions = ['delete_selected_recipes', 'publish_recipes', 'unpublish_recipes']
    
    def delete_selected_recipes(self, request, queryset):
        """Custom delete action with confirmation message."""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f'Successfully deleted {count} recipe(s).',
            messages.SUCCESS
        )
    delete_selected_recipes.short_description = "Delete selected recipes"
    
    def publish_recipes(self, request, queryset):
        """Bulk publish recipes."""
        count = queryset.update(is_published=True)
        self.message_user(
            request,
            f'Successfully published {count} recipe(s).',
            messages.SUCCESS
        )
    publish_recipes.short_description = "Publish selected recipes"
    
    def unpublish_recipes(self, request, queryset):
        """Bulk unpublish recipes."""
        count = queryset.update(is_published=False)
        self.message_user(
            request,
            f'Successfully unpublished {count} recipe(s).',
            messages.SUCCESS
        )
    unpublish_recipes.short_description = "Unpublish selected recipes"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
    search_fields = ("follower__username", "followed__username")
    autocomplete_fields = ("follower", "followed")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "first_name", "last_name")
    search_fields = ("username", "email", "first_name", "last_name")
