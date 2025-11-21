from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from recipes.forms import RecipeForm
from recipes.models import Follow, Recipe, User


class RecipeListView(ListView):
    """Display all published recipes."""

    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 10

    def get_queryset(self):
        return Recipe.objects.filter(is_published=True).select_related("author")


class RecipeDetailView(DetailView):
    """Display a single recipe."""

    model = Recipe
    template_name = "recipes/recipe_detail.html"
    context_object_name = "recipe"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and self.object.author != user:
            context["is_following_author"] = Follow.objects.filter(
                follower=user, followed=self.object.author
            ).exists()
        return context


class RecipeAuthorRequiredMixin(UserPassesTestMixin):
    """Ensure the current user authored the recipe."""

    def test_func(self):
        recipe = self.get_object()
        return recipe.author == self.request.user

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "You do not have permission to edit this recipe.")
        return redirect("recipe_detail", pk=self.get_object().pk)


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """Allow authenticated users to publish new recipes."""

    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"
    extra_context = {
        "page_title": "Publish a recipe",
        "submit_label": "Publish recipe",
    }

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Your recipe has been published.")
        return response

    def get_success_url(self):
        return reverse("recipe_detail", kwargs={"pk": self.object.pk})


class RecipeUpdateView(LoginRequiredMixin, RecipeAuthorRequiredMixin, UpdateView):
    """Allow authors to edit their recipes."""

    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"
    extra_context = {
        "page_title": "Update your recipe",
        "submit_label": "Update recipe",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your recipe has been updated.")
        return response

    def get_success_url(self):
        return reverse("recipe_detail", kwargs={"pk": self.object.pk})


class FeedView(LoginRequiredMixin, ListView):
    """Display recipes from authors the user follows."""

    template_name = "recipes/feed.html"
    model = Recipe
    context_object_name = "recipes"
    paginate_by = 10

    def get_queryset(self):
        followed_users = self.request.user.following.values_list("followed", flat=True)
        return (
            Recipe.objects.filter(author__in=followed_users, is_published=True)
            .select_related("author")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_followed_users"] = self.request.user.following.exists()
        return context


@login_required
def follow_user(request, user_id):
    """Create a follow relationship."""

    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        messages.error(request, "You cannot follow yourself.")
    else:
        Follow.objects.get_or_create(follower=request.user, followed=target)
        messages.success(request, f"You are now following {target.username}.")
    return redirect(request.META.get("HTTP_REFERER", reverse_lazy("feed")))


@login_required
def unfollow_user(request, user_id):
    """Remove a follow relationship."""

    target = get_object_or_404(User, pk=user_id)
    Follow.objects.filter(follower=request.user, followed=target).delete()
    messages.info(request, f"You unfollowed {target.username}.")
    return redirect(request.META.get("HTTP_REFERER", reverse_lazy("feed")))

