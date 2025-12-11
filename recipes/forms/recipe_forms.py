from django import forms
from recipes.models import Recipe


class RecipeForm(forms.ModelForm):
    """Form used for creating and updating recipes."""

    class Meta:
        model = Recipe
        fields = [
            "title",
            "summary",
            "ingredients",
            "instructions",
            "dietary_requirement",
            "difficulty",
            "prep_time_minutes",
            "cook_time_minutes",
            "servings",
            "image",        
        ]
        widgets = {
            "ingredients": forms.Textarea(attrs={"rows": 5}),
            "instructions": forms.Textarea(attrs={"rows": 8}),
            "dietary_requirement": forms.Select(),
            "difficulty": forms.Select(),
        }

    def clean_ingredients(self):
        ingredients = self.cleaned_data.get("ingredients", "").strip()
        if not ingredients:
            raise forms.ValidationError("Please provide at least one ingredient.")
        return ingredients

    def clean_instructions(self):
        instructions = self.cleaned_data.get("instructions", "").strip()
        if not instructions:
            raise forms.ValidationError("Please provide the cooking instructions.")
        return instructions


