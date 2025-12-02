from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from recipes.models import Comment, Recipe
from recipes.forms import CommentForm


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.recipe = recipe
            comment.user = request.user
            comment.save()

        # Recipe detail URL uses `pk` as the kwarg name
        return redirect("recipe_detail", pk=recipe.id)

    def get(self, request, recipe_id):
        """Optional standalone page to add a comment (not required for modal usage)."""

        recipe = get_object_or_404(Recipe, pk=recipe_id)
        form = CommentForm()
        return render(
            request,
            "recipes/add_comment.html",
            {"form": form, "recipe": recipe},
        )