# In profile_view.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from recipes.models import SavedRecipe, Recipe

@login_required
def profile(request):
    current_user = request.user
    
    # Handle favorite toggle
    if request.method == 'POST' and 'recipe_id' in request.POST:
        recipe_id = request.POST['recipe_id']
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            saved_recipe, created = SavedRecipe.objects.get_or_create(
                user=current_user,
                recipe=recipe
            )
            if not created:
                saved_recipe.delete()
        except Recipe.DoesNotExist:
            pass
        
        # Stay on the same tab - FIXED
        tab = request.GET.get('tab', '')
        if tab:
            # Use reverse to get the URL and then add the query parameter
            return redirect(f"{reverse('profile')}?tab={tab}")
        return redirect('profile')
    
    # Normal GET request - use prefetch_related for better performance
    saved_recipes_relations = current_user.saved_recipes.select_related('recipe__created_by').all()
    
    # Extract the actual Recipe objects
    saved_recipes = [saved_recipe.recipe for saved_recipe in saved_recipes_relations]
    saved_recipe_ids = [recipe.id for recipe in saved_recipes]
    
    context = {
        'user': current_user,
        'saved_recipe_ids': saved_recipe_ids,
        'saved_recipes': saved_recipes,
    }
    
    return render(request, 'profile.html', context)