from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from recipes.models import Recipe, SavedRecipe

@login_required
def dashboard(request):
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
        return redirect('dashboard')  # Refresh the page
    
    # Normal GET request
    recipes = Recipe.objects.all().select_related('created_by')
    saved_recipe_ids = SavedRecipe.objects.filter(user=current_user).values_list('recipe_id', flat=True)
    
    context = {
        'user': current_user,
        'recipes': recipes,
        'saved_recipe_ids': list(saved_recipe_ids),
    }
    return render(request, 'dashboard.html', context)