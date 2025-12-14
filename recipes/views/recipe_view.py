from recipes.forms import CommentForm


def add_comment_form_to_context(view_instance, context):
    """
    Helper used to enrich an existing recipe detail context with
    the comment form expected by the comment feature.

    This file is intentionally small – the main logic lives in
    `RecipeDetailView.get_context_data` in `recipe_views.py`.
    """

    context["comment_form"] = CommentForm()
    return context
