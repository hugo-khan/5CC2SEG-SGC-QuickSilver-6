from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from recipes.forms import RecipeForm, CommentForm
from recipes.models import Comment, Follow, Recipe, SavedRecipe, User


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
        """
        Combine the original recipe detail context (follow status etc.)
        with the additional data needed for comments and likes.
        """

        context = super().get_context_data(**kwargs)
        recipe = self.object
        user = self.request.user

        # Follow flag from the original implementation
        if user.is_authenticated and recipe.author != user:
            context["is_following_author"] = Follow.objects.filter(
                follower=user,
                followed=recipe.author,
            ).exists()

        # Comment feature: full comment list and form
        comments = Comment.objects.filter(recipe=recipe).select_related("user")
        context["comments"] = list(comments)
        context["comment_form"] = CommentForm()

        # Like feature: expose convenience flags/counters
        context["total_likes"] = recipe.likes.count()
        context["has_liked"] = (
            user.is_authenticated and recipe.likes.filter(pk=user.pk).exists()
        )

        # Favourite feature: check if recipe is saved by current user
        context["is_favourited"] = (
            user.is_authenticated
            and SavedRecipe.objects.filter(user=user, recipe=recipe).exists()
        )

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
        """
        Extend the original feed context with a mapping of
        recipe.id -> top 3 newest comments, as expected by the
        comment feature tests.
        """

        context = super().get_context_data(**kwargs)
        context["has_followed_users"] = self.request.user.following.exists()

        recipes = context.get("object_list", [])
        comments_by_recipe = {}

        if recipes:
            comments = (
                Comment.objects.filter(recipe__in=recipes)
                .select_related("user", "recipe")
                .order_by("-created_at")
            )
            for recipe in recipes:
                recipe_comments = [c for c in comments if c.recipe_id == recipe.id][:3]
                comments_by_recipe[recipe.id] = recipe_comments

        context["comments"] = comments_by_recipe
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


@login_required
def toggle_save_recipe(request, pk):
    """Toggle save/unsave a recipe (favourite). POST-only, redirects back to recipe detail."""

    recipe = get_object_or_404(Recipe, pk=pk)

    if request.method == "POST":
        saved_recipe, created = SavedRecipe.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            saved_recipe.delete()
            messages.info(request, f"Removed '{recipe.title}' from favourites.")
        else:
            messages.success(request, f"Added '{recipe.title}' to favourites.")

    return redirect("recipe_detail", pk=pk)

