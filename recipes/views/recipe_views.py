from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView

from recipes.forms import RecipeForm, CommentForm, CommentReportForm
from recipes.forms.recipe_filter_form import RecipeFilterForm
from recipes.helpers import collect_all_ingredients
from recipes.models import Comment, Follow, Recipe, SavedRecipe, User


class RecipeListView(ListView):
    """Display all published recipes."""

    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 10

    def get_queryset(self):
        recipes = Recipe.objects.filter(is_published=True).select_related("author")

        #filtering, for ingredients, dietary requirements
        self.form = RecipeFilterForm(self.request.GET or None)
        all_ingredients = collect_all_ingredients()
        self.form.fields["ingredients"].queryset = all_ingredients

    def get_context_data(self, **kwargs):
        """
        Include the requesting user's recipes so the browse page can show
        both personal and global lists side by side.
        """

        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context["my_recipes"] = (
                Recipe.objects.filter(author=self.request.user, is_published=True)
                .select_related("author")
                .order_by("-created_at")
            )
        else:
            context["my_recipes"] = []

        return context


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

        # Share feature: generate share URL
        context["share_url"] = recipe.get_share_url(self.request)

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


class RecipeDeleteView(LoginRequiredMixin, RecipeAuthorRequiredMixin, DeleteView):
    """Allow authors to delete their recipes."""

    model = Recipe
    template_name = "recipes/recipe_confirm_delete.html"
    success_url = reverse_lazy("recipe_list")

    def delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        messages.success(self.request, f'Recipe "{recipe.title}" has been deleted.')
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "You do not have permission to delete this recipe.")
        return redirect("recipe_detail", pk=self.get_object().pk)


class FeedView(LoginRequiredMixin, ListView):
    """Display recipes from authors the user follows."""

    template_name = "recipes/feed.html"
    model = Recipe
    context_object_name = "recipes"
    paginate_by = 10

    def get_queryset(self):
        followed_users = self.request.user.following.values_list("followed", flat=True)
        recipes = Recipe.objects.filter(author__in=followed_users, is_published=True).select_related("author").order_by("-created_at")


        #filtering for feed page - form for filtering
        self.form = RecipeFilterForm(self.request.GET or None)

        #ingredient filtering
        all_ingredients = collect_all_ingredients()
        self.form.fields['ingredients'].choices = [(i,i.title()) for i in all_ingredients]
        selected_ingredients = self.request.GET.getlist('ingredients')
        if selected_ingredients:
            for ingredient in selected_ingredients:
                recipes = recipes.filter(ingredients__icontains=ingredient)

        return recipes

    def get_context_data(self, **kwargs):
        """
        Extend the original feed context with a mapping of
        recipe.id -> top 3 newest comments, as expected by the
        comment feature tests.
        """

        context = super().get_context_data(**kwargs)
        context["has_followed_users"] = self.request.user.following.exists()

        # Add saved_recipe_ids for favourite state display
        saved_recipe_ids = SavedRecipe.objects.filter(
            user=self.request.user
        ).values_list("recipe_id", flat=True)
        context["saved_recipe_ids"] = list(saved_recipe_ids)

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
    """Toggle save/unsave a recipe (favourite). POST-only, redirects back to referring page."""

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

    # Redirect back to referring page, or recipe detail as fallback
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("recipe_detail", pk=pk)
