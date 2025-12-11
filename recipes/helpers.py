### Helper function and classes go here.
from recipes.models import Recipe

#This function gets every single ingredient used from all recipes - used for filtering by ingredient
def collect_all_ingredients():
    all_ingredients = set()
    for r in Recipe.objects.all():
        if r.ingredients:
            items = [i.strip().lower() for i in r.ingredients.split(',')]
            all_ingredients.update(items)
    return sorted(all_ingredients)