from django.urls import path

from recipes.views import (
    FeedView,
    RecipeCreateView,
    RecipeDeleteView,
    RecipeDetailView,
    RecipeUpdateView,
    RecipeShareView,
    follow_user,
    unfollow_user,
)
from recipes.views.dashboard_view import browse_recipes
from recipes.views.recipe_views import toggle_save_recipe

urlpatterns = [
    path("recipes/", browse_recipes, name="recipe_list"),
    path("recipes/new/", RecipeCreateView.as_view(), name="recipe_create"),
    path("recipes/<int:pk>/", RecipeDetailView.as_view(), name="recipe_detail"),
    path("recipes/<int:pk>/edit/", RecipeUpdateView.as_view(), name="recipe_edit"),
    path("recipes/<int:pk>/delete/", RecipeDeleteView.as_view(), name="recipe_delete"),
    path("recipes/<int:pk>/save/", toggle_save_recipe, name="toggle_save_recipe"),
    path("share/<uuid:share_token>/", RecipeShareView.as_view(), name="recipe_share"),
    path("feed/", FeedView.as_view(), name="feed"),
    path("follow/<int:user_id>/", follow_user, name="follow_user"),
    path("unfollow/<int:user_id>/", unfollow_user, name="unfollow_user"),
]


