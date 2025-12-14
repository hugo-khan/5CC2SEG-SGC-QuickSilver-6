from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from recipes.forms.recipe_filter_form import RecipeFilterForm
from recipes.models import Recipe


def recipe_search(request):
    recipes = Recipe.objects.all()

    # Search by name or description
    if request.GET.get("search"):
        search_term = request.GET.get("search")
        recipes = recipes.filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term)
        )

    # Filter by dietary requirements
    dietary_filters = request.GET.getlist("dietary_requirement")
    if dietary_filters:
        recipes = recipes.filter(dietary_requirement__in=dietary_filters)

    # Sort by (defaults to newest first)
    sort_by = request.GET.get("sort_by", "date")
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
        "form": RecipeFilterForm(request.GET or None),
        "page_obj": page_obj,
        "recipes": page_obj.object_list,
        "querystring": query_params.urlencode(),
        "selected_dietary": dietary_filters,
    }

    return render(request, "recipes_search.html", context)
