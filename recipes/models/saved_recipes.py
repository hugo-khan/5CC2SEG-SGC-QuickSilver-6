from django.test import TestCase
from django.contrib.auth.models import User
from .models import SavedRecipe
from .recipe import Recipe
from django.utils import timezone


class SavedRecipeModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

        self.recipe = Recipe.objects.create(title='Spaghetti Bolognese', description='A tasty pasta dish')

    def test_save_recipe(self):
        """Test that a user can save a recipe."""
        # Save the recipe
        saved_recipe = SavedRecipe.objects.create(user=self.user, recipe=self.recipe)

        # Check that the SavedRecipe instance is saved correctly
        self.assertEqual(saved_recipe.user, self.user)
        self.assertEqual(saved_recipe.recipe, self.recipe)
        self.assertIsInstance(saved_recipe.saved_at, timezone.datetime)  # Ensure that saved_at is set

    def test_unique_together_constraint(self):
        """Test that a user can't save the same recipe twice."""
        SavedRecipe.objects.create(user=self.user, recipe=self.recipe)

        with self.assertRaises(Exception):  # Expect an exception due to the unique constraint
            SavedRecipe.objects.create(user=self.user, recipe=self.recipe)

    def test_saved_recipe_ordering(self):
        """Test that SavedRecipe objects are ordered by saved_at in descending order."""
        # Create two different recipes
        recipe2 = Recipe.objects.create(title='Chicken Curry', description='Spicy chicken curry')

        # Save the recipes
        SavedRecipe.objects.create(user=self.user, recipe=self.recipe)
        SavedRecipe.objects.create(user=self.user, recipe=recipe2)

        # Fetch saved recipes and check the order
        saved_recipes = SavedRecipe.objects.all()

        # Assert that the most recently saved recipe comes first
        self.assertEqual(saved_recipes[0].recipe.title, 'Chicken Curry')
        self.assertEqual(saved_recipes[1].recipe.title, 'Spaghetti Bolognese')

    def test_string_representation(self):
        """Test the string representation of SavedRecipe."""
        saved_recipe = SavedRecipe.objects.create(user=self.user, recipe=self.recipe)

        # Check that the string representation is in the expected format
        self.assertEqual(str(saved_recipe), "testuser saved Spaghetti Bolognese")
