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

@register.filter
def get_heart_icon(recipe_id, saved_recipe_ids):
    """Return the appropriate heart icon class."""
    if recipe_id in saved_recipe_ids:
        return "bi-heart-fill"
    return "bi-heart"

@register.filter
def map_attribute(items, attribute_name):
    """
    Extract an attribute from each item in a list.
    Usage: {{ object_list|map_attribute:"field_name" }}
    """
    if not items:
        return []
    
    try:
        return [getattr(item, attribute_name) for item in items]
    except (AttributeError, TypeError):
        return []

# Alternative implementation using dictionary access if needed
@register.filter
def map_key(items, key_name):
    """
    Extract a key from each dictionary in a list.
    Usage: {{ dict_list|map_key:"key_name" }}
    """
    if not items:
        return []
    
    try:
        return [item.get(key_name) for item in items]
    except (AttributeError, TypeError):
        return []


@register.filter
def get_item(dictionary, key):
    """
    Look up a value from a dictionary by key.
    Usage: {{ my_dict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None