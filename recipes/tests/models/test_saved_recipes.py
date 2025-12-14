from django.test import TestCase
from django.contrib.auth import get_user_model
from recipes.models import Recipe, SavedRecipe
from django.db import IntegrityError

User = get_user_model()

class SavedRecipeModelTests(TestCase):
    fixtures = ["default_user.json", "other_users.json", "recipes.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="password123")
        self.chocolate_cake = Recipe.objects.get(pk=1)
        self.spaghetti = Recipe.objects.get(pk=6)

    def test_user_can_save_recipe(self):
        saved = SavedRecipe.objects.create(
            user=self.user,
            recipe=self.spaghetti
        )
        self.assertEqual(saved.user, self.user)
        self.assertEqual(saved.recipe, self.spaghetti)

    def test_user_cannot_save_same_recipe_twice(self):
        SavedRecipe.objects.create(user=self.user, recipe=self.spaghetti)
        with self.assertRaises(IntegrityError):
            SavedRecipe.objects.create(user=self.user, recipe=self.spaghetti)

    def test_saved_recipe_ordering(self):
        first = SavedRecipe.objects.create(user=self.user, recipe=self.chocolate_cake)
        second = SavedRecipe.objects.create(user=self.user, recipe=self.spaghetti)

        saved_list = list(SavedRecipe.objects.filter(user=self.user))

        self.assertEqual(saved_list[0], second)
        self.assertEqual(saved_list[1], first)

    def test_string_representation(self):
        saved = SavedRecipe.objects.create(user=self.user, recipe=self.spaghetti)
        self.assertEqual(str(saved), "alice saved Spaghetti Bolognese")

