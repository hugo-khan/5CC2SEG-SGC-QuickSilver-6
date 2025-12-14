from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DeleteView

from recipes.models import Comment


class CommentAuthorRequiredMixin(UserPassesTestMixin):
    """Ensure only the comment author can delete their comment."""

    def test_func(self):
        comment = self.get_object()
        return comment.user == self.request.user


class CommentDeleteView(LoginRequiredMixin, CommentAuthorRequiredMixin, DeleteView):
    """Allow comment authors to delete their comments."""

    model = Comment
    template_name = "recipes/comment_confirm_delete.html"

    def get_success_url(self):
        """Redirect back to the recipe detail page after deletion."""
        comment = self.get_object()
        recipe_pk = comment.recipe.pk
        # Delete the comment first, then redirect
        return reverse("recipe_detail", kwargs={"pk": recipe_pk})

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        recipe_pk = comment.recipe.pk
        messages.success(self.request, "Your comment has been deleted.")
        response = super().delete(request, *args, **kwargs)
        # Redirect to the recipe detail page
        return redirect("recipe_detail", pk=recipe_pk)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        comment = self.get_object()
        messages.error(
            self.request, "You do not have permission to delete this comment."
        )
        return redirect("recipe_detail", pk=comment.recipe.pk)
