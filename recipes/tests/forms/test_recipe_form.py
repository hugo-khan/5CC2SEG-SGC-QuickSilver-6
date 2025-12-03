from django.test import TestCase

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


