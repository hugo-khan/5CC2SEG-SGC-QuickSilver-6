from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from recipes.forms.recipe_filter_form import RecipeFilterForm
from recipes.helpers import collect_all_ingredients
from recipes.models import Recipe


def author_recipes(request, author_id):
    author = get_object_or_404(get_user_model(), id=author_id)
    recipes = Recipe.objects.filter(author=author)
    form = RecipeFilterForm(request.GET or None)

    # Filter by ingredients
    form.fields["ingredients"].choices = [
        (i, i.title()) for i in collect_all_ingredients()
    ]
    selected_ingredients = request.GET.getlist("ingredients")
    if selected_ingredients:
        for ingredient in selected_ingredients:
            recipes = recipes.filter(ingredients__icontains=ingredient)
    # Search by name
    search_term = (request.GET.get("search") or "").strip()
    if search_term:
        recipes = recipes.filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term)
        )

    # Filter by dietary requirements
    dietary_filters = [
        item for item in request.GET.getlist("dietary_requirement") if item
    ]
    if dietary_filters:
        recipes = recipes.filter(dietary_requirement__in=dietary_filters)

    # Sort by
    sort_by = request.GET.get("sort_by") or "date"
    if sort_by == "date":
        recipes = recipes.order_by("-date_posted")
    elif sort_by == "-date":
        recipes = recipes.order_by("date_posted")
    elif sort_by == "popularity":
        recipes = recipes.order_by("-popularity")
    elif sort_by == "-popularity":
        recipes = recipes.order_by("popularity")
    elif sort_by == "name":
        recipes = recipes.order_by("name")

    # Pagination
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "author": author,
        "search_value": search_term,
        "current_sort": sort_by,
        "selected_dietary": dietary_filters,
        "dietary_choices": Recipe.DIETARY_CHOICES,
        "page_obj": page_obj,
        "recipes": page_obj.object_list,
        "querystring": query_params.urlencode(),
    }

    return render(request, "author_recipes.html", context)
