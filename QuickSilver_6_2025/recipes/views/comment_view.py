from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Recipe, Comment
from .forms import CommentForm


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.recipe = recipe
            comment.user = request.user
            comment.save()

        return redirect('recipe_detail', recipe_id=recipe.id)

    def get(self, request, recipe_id):
        """Only needed if you want a separate page for comments.
           If you're using a modal popup, you likely won't use GET."""
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        form = CommentForm()
        return render(request, 'recipes/add_comment.html', {'form': form, 'recipe': recipe})