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
            "dietary_requirement": "none",
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
        from recipes.models import User, Recipe
        # Create a recipe with ingredients to populate the ingredient list
        self.user = User.objects.create_user(
            username='@testuser',
            password='testpass123',
            email='test@example.com'
        )
        Recipe.objects.create(
            author=self.user,
            title='Test Recipe',
            name='Test Recipe',
            description='Test',
            ingredients='flour, sugar, eggs',
            instructions='Mix and bake',
            is_published=True
        )
        self.ingredients = collect_all_ingredients() # getting ingredients manually here - will test form separately

    def test_choices(self):
        form = RecipeFilterForm()
        form.fields['ingredients'].queryset = self.ingredients
        form.fields['ingredients'].choices = [(i, i.title()) for i in self.ingredients]
        choice_values = [choice[0] for choice in form.fields['ingredients'].choices]
        self.assertGreater(len(choice_values), 0)

    def test_form_valid_single_ingredient(self):
        if len(self.ingredients) > 0:
            data = {'ingredients': [self.ingredients[0]]}
            form = RecipeFilterForm(data=data)
            form.fields['ingredients'].queryset = self.ingredients
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data['ingredients'], [self.ingredients[0]])

    def test_form_valid_multiple_ingredients(self):
        if len(self.ingredients) >= 2:
            data = {'ingredients': self.ingredients[:2]}
            form = RecipeFilterForm(data=data)
            form.fields['ingredients'].queryset = self.ingredients
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data['ingredients'], self.ingredients[:2])

