from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth.models import User
from recipes.models import Recipe
from recipes.forms.recipe_filter_form import RecipeFilterForm
from django.core.paginator import Paginator

def author_recipes(request, author_id):
    author = get_object_or_404(User, id=author_id)
    recipes = Recipe.objects.filter(author=author)
    form = RecipeFilterForm(request.GET or None)
    
    # Search by name
    if request.GET.get('search'):
        search_term = request.GET.get('search')
        recipes = recipes.filter(
            Q(name__icontains=search_term) | 
            Q(description__icontains=search_term)
        )
    
    # Filter by dietary requirements
    dietary_filters = request.GET.getlist('dietary_requirement')
    if dietary_filters:
        recipes = recipes.filter(dietary_requirement__in=dietary_filters)
    
    # Sort by
    sort_by = request.GET.get('sort_by', 'date')
    if sort_by == 'date':
        recipes = recipes.order_by('-date_posted')
    elif sort_by == '-date':
        recipes = recipes.order_by('date_posted')
    elif sort_by == 'popularity':
        recipes = recipes.order_by('-popularity')
    elif sort_by == '-popularity':
        recipes = recipes.order_by('popularity')
    elif sort_by == 'name':
        recipes = recipes.order_by('name')
    
    # Pagination
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'author': author,
        'form': form,
        'page_obj': page_obj,
        'recipes': page_obj.object_list,
    }
    
    return render(request, 'author_recipes.html', context)