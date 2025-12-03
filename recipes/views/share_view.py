from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from recipes.models import Recipe


class RecipeShareView(DetailView):
    """
    Public view for sharing recipes via share token.
    Allows anyone with the share link to view the recipe,
    even if they're not logged in.
    """

    model = Recipe
    template_name = "recipes/recipe_share.html"
    context_object_name = "recipe"
    slug_field = "share_token"
    slug_url_kwarg = "share_token"

    def get_queryset(self):
        """Only allow sharing of published recipes."""
        return Recipe.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        """Add share URL and other context for the share view."""
        context = super().get_context_data(**kwargs)
        recipe = self.object
        context["share_url"] = recipe.get_share_url(self.request)
        context["is_shared_view"] = True
        return context

