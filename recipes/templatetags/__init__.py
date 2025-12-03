from django import template

register = template.Library()

@register.filter
def get_difficulty_class(difficulty):
    """Return CSS class for difficulty badge."""
    difficulty_classes = {
        'easy': 'difficulty-easy',
        'medium': 'difficulty-medium', 
        'hard': 'difficulty-hard',
    }
    return difficulty_classes.get(difficulty.lower(), 'difficulty-easy')

@register.filter
def format_cooking_time(minutes):
    """Format cooking time in a readable way."""
    if minutes < 60:
        return f"{minutes}min"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins > 0:
            return f"{hours}h {mins}min"
        else:
            return f"{hours}h"

@register.filter
def is_recipe_saved(recipe_id, saved_recipe_ids):
    """Check if a recipe is saved by the current user."""
    return recipe_id in saved_recipe_ids