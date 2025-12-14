from django.test import TestCase

from recipes.forms import RecipeForm
from recipes.forms.recipe_filter_form import RecipeFilterForm
from recipes.helpers import collect_all_ingredients


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
    @classmethod
    def setUpTestData(cls):
        from recipes.models import Recipe, User

        cls.user = User.objects.create_user(
            username="@testuser",
            password="testpass123",
            email="test@example.com",
        )
        Recipe.objects.create(
            author=cls.user,
            title="Test Recipe",
            name="Test Recipe",
            description="Test",
            ingredients="flour, sugar, eggs",
            instructions="Mix and bake",
            is_published=True,
        )
        cls.ingredients = collect_all_ingredients()

    def setUp(self):
        self.form = RecipeFilterForm()
        self._populate_ingredients_field(self.form)

    def _populate_ingredients_field(self, form):
        form.fields["ingredients"].queryset = self.ingredients
        form.fields["ingredients"].choices = [
            (ingredient, ingredient.title()) for ingredient in self.ingredients
        ]

    def test_choices(self):
        choice_values = [
            choice[0] for choice in self.form.fields["ingredients"].choices
        ]
        self.assertGreater(len(choice_values), 0)

    def test_form_valid_single_ingredient(self):
        if len(self.ingredients) > 0:
            selected = [self.ingredients[0]]
            form = RecipeFilterForm(data={"ingredients": selected})
            self._populate_ingredients_field(form)
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data["ingredients"], selected)

    def test_form_valid_multiple_ingredients(self):
        if len(self.ingredients) >= 2:
            selected = self.ingredients[:2]
            form = RecipeFilterForm(data={"ingredients": selected})
            self._populate_ingredients_field(form)
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data["ingredients"], selected)
