from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from recipes.models import Recipe, SavedRecipe


@login_required
def profile(request):
    current_user = request.user

    # Handle favorite toggle
    if request.method == "POST" and "recipe_id" in request.POST:
        recipe_id = request.POST["recipe_id"]
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            saved_recipe, created = SavedRecipe.objects.get_or_create(
                user=current_user, recipe=recipe
            )
            if not created:
                saved_recipe.delete()
        except Recipe.DoesNotExist:
            pass

        # Stay on the same tab
        tab = request.GET.get("tab", "")
        if tab:
            return redirect(f"profile?tab={tab}")
        return redirect("profile")

    # Normal GET request
    saved_recipes = current_user.saved_recipes.all().select_related(
        "recipe", "recipe__author"
    )
    saved_recipe_ids = saved_recipes.values_list("recipe_id", flat=True)

    return render(
        request,
        "profile.html",
        {
            "user": current_user,
            "saved_recipe_ids": list(saved_recipe_ids),
            "saved_recipes_prefetched": saved_recipes,
        },
    )
