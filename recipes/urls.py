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
from recipes.views.ai_chatbot_view import (
    ai_chatbot,
    ai_chatbot_message,
    ai_chatbot_publish,
    ai_chatbot_clear,
    ai_diagnostic,
)

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
    # AI Chef chatbot
    path("ai/chef/", ai_chatbot, name="ai_chatbot"),
    path("ai/chef/message/", ai_chatbot_message, name="ai_chatbot_message"),
    path("ai/chef/publish/<int:draft_id>/", ai_chatbot_publish, name="ai_chatbot_publish"),
    path("ai/chef/clear/", ai_chatbot_clear, name="ai_chatbot_clear"),
    path("ai/chef/diagnostic/", ai_diagnostic, name="ai_diagnostic"),
]


