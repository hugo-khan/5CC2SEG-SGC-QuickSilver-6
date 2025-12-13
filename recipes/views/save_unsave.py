# recipes/views/toggle_save.py
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from recipes.models import Recipe, SavedRecipe

@login_required
@require_POST
def toggle_save_recipe(request, pk):
    """Toggle save/unsave a recipe."""
    recipe = get_object_or_404(Recipe, pk=pk)
    saved_recipe, created = SavedRecipe.objects.get_or_create(
        user=request.user,
        recipe=recipe
    )
    
    if not created:
        # If it already existed, delete it (toggle off)
        saved_recipe.delete()
        is_saved = False
    else:
        is_saved = True
    
    return JsonResponse({'is_saved': is_saved})