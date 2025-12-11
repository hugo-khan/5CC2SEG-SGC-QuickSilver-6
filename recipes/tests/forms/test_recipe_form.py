from django.test import TestCase
from recipes.helpers import collect_all_ingredients
from recipes.forms.recipe_filter_form import RecipeFilterForm
from recipes.forms import RecipeForm


class RecipeFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "title": "Cake",
            "summary": "Tasty cake",
            "ingredients": "Flour\nSugar",
            "instructions": "Mix\nBake",
            "prep_time_minutes": 10,
            "cook_time_minutes": 30,
            "servings": 4,
            "is_published": True,
        }

    def test_form_valid(self):
        form = RecipeForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_missing_instructions_invalid(self):
        data = self.valid_data.copy()
        data["instructions"] = "   "
        form = RecipeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("instructions", form.errors)

class RecipeFilterFormTest(TestCase):
    def setUp(self):
        self.ingredients = collect_all_ingredients() # getting ingredients manually here - will test form separately

    def test_choices(self):
        form = RecipeFilterForm()
        form.fields['ingredients'].choices = [(i, i.title()) for i in self.ingredients]
        choice_values = [choice[0] for choice in form.fields['ingredients'].choices]
        self.assertListEqual(choice_values, self.ingredients)

    def test_form_valid_single_ingredient(self):

        data = {'ingredients': [self.ingredients[0]]}
        form = RecipeFilterForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['ingredients'], [self.ingredients[0]])

    def test_form_valid_multiple_ingredients(self):
        data = {'ingredients': self.ingredients[:2]}
        form = RecipeFilterForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['ingredients'], self.ingredients[:2])

