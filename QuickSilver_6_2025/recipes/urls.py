from django.urls import path

from recipes.views import (
    FeedView,
    RecipeCreateView,
    RecipeDetailView,
    RecipeListView,
    RecipeUpdateView,
    follow_user,
    unfollow_user,
)

urlpatterns = [
    path("recipes/", RecipeListView.as_view(), name="recipe_list"),
    path("recipes/new/", RecipeCreateView.as_view(), name="recipe_create"),
    path("recipes/<int:pk>/", RecipeDetailView.as_view(), name="recipe_detail"),
    path("recipes/<int:pk>/edit/", RecipeUpdateView.as_view(), name="recipe_edit"),
    path("feed/", FeedView.as_view(), name="feed"),
    path("follow/<int:user_id>/", follow_user, name="follow_user"),
    path("unfollow/<int:user_id>/", unfollow_user, name="unfollow_user"),
]


