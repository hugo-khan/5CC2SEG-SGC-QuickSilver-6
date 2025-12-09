from django.urls import path

from recipes.views import (
    FeedView,
    RecipeCreateView,
    RecipeDetailView,
    RecipeUpdateView,
    follow_user,
    unfollow_user,
    comment_report_view,
    reported_comments_view
)
from recipes.views.comment_report_view import report_comment
from recipes.views.dashboard_view import browse_recipes
from recipes.views.recipe_views import toggle_save_recipe
from recipes.views.reported_comments_view import reported_comments_view, delete_reported_comment

urlpatterns = [
    path("recipes/", browse_recipes, name="recipe_list"),
    path("recipes/new/", RecipeCreateView.as_view(), name="recipe_create"),
    path("recipes/<int:pk>/", RecipeDetailView.as_view(), name="recipe_detail"),
    path("recipes/<int:pk>/edit/", RecipeUpdateView.as_view(), name="recipe_edit"),
    path("recipes/<int:pk>/save/", toggle_save_recipe, name="toggle_save_recipe"),
    path("feed/", FeedView.as_view(), name="feed"),
    path("follow/<int:user_id>/", follow_user, name="follow_user"),
    path("unfollow/<int:user_id>/", unfollow_user, name="unfollow_user"),
    path("comments/report/",report_comment, name="report_comments"),
    path("admin/reported-comments/",reported_comments_view, name="reported_comments"),
    ]


