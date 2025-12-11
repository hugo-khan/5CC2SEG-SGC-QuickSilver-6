from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from recipes.forms.recipe_filter_form import RecipeFilterForm
from recipes.helpers import collect_all_ingredients
from recipes.models import Recipe, SavedRecipe


@login_required
@never_cache
def dashboard(request):
    """Display welcome page for logged-in users."""
    return render(request, "dashboard_welcome.html", {"user": request.user})


@login_required
@never_cache
def browse_recipes(request):
    """Display all recipes with favourite toggle functionality."""
    current_user = request.user

    # Handle favourite toggle
    if request.method == "POST" and "recipe_id" in request.POST:
        recipe_id = request.POST["recipe_id"]
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            saved_recipe, created = SavedRecipe.objects.get_or_create(
                user=current_user,
                recipe=recipe,
            )
            if not created:
                saved_recipe.delete()
        except Recipe.DoesNotExist:
            pass
        return redirect("recipe_list")  # Refresh the page

    # Normal GET request: show all recipes with saved-state information
    recipes = Recipe.objects.all().select_related("author")
    
    # Set up filter form with ingredient choices
    form = RecipeFilterForm(request.GET or None)
    all_ingredients = collect_all_ingredients()
    form.fields['ingredients'].choices = [(i, i.title()) for i in all_ingredients]
    
    # Filter by selected ingredients
    selected_ingredients = request.GET.getlist('ingredients')
    if selected_ingredients:
        for ingredient in selected_ingredients:
            recipes = recipes.filter(ingredients__icontains=ingredient)
    
    my_recipes = (
        Recipe.objects.filter(author=current_user)
        .select_related("author")
        .order_by("-created_at")
    )
    saved_recipe_ids = SavedRecipe.objects.filter(user=current_user).values_list(
        "recipe_id", flat=True
    )

    context = {
        "user": current_user,
        "recipes": recipes,
        "my_recipes": my_recipes,
        "saved_recipe_ids": list(saved_recipe_ids),
        "form": form,
        "selected_ingredients": selected_ingredients,
    }
    return render(request, "dashboard.html", context)
