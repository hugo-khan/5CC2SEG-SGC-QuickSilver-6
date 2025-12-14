from django.test import TestCase

from recipes.models.recipe import Recipe
from recipes.models.user import User


class TestLikeModel(TestCase):

    def _create_recipe(self, author=None):
        user = author or User.objects.create_user(
            username="@author", email="author@example.com", password="pass123"
        )
        return Recipe.objects.create(
            author=user,
            title="Test",
            name="Test",
            description="test",
            ingredients="a,b",
            instructions="mix",
            is_published=True,
        )

    def test_recipe_has_likes_field(self):
        """Ensure Recipe model contains a ManyToManyField named 'likes'."""
        recipe = self._create_recipe()
        self.assertTrue(hasattr(recipe, "likes"))

    def test_user_can_like_recipe(self):
        """User should be able to like a recipe."""
        user = User.objects.create_user(
            username="@u1", email="u1@example.com", password="pass123"
        )
        recipe = self._create_recipe(user)

        recipe.likes.add(user)

        self.assertIn(user, recipe.likes.all())
        self.assertEqual(recipe.likes.count(), 1)

    def test_user_can_unlike_recipe(self):
        """User can remove a like from a recipe."""
        user = User.objects.create_user(
            username="@u1", email="u1@example.com", password="pass123"
        )
        recipe = Recipe.objects.create(title="Test", description="test")

        recipe.likes.add(user)
        recipe.likes.remove(user)

        self.assertNotIn(user, recipe.likes.all())
        self.assertEqual(recipe.likes.count(), 0)

    def test_multiple_users_can_like_same_recipe(self):
        """More than one user may like a recipe."""
        u1 = User.objects.create_user(username="@u1", email="a@a.com", password="123")
        u2 = User.objects.create_user(username="@u2", email="b@b.com", password="123")

        recipe = self._create_recipe(u1)

        recipe.likes.add(u1)
        recipe.likes.add(u2)

        self.assertEqual(recipe.likes.count(), 2)
        self.assertIn(u1, recipe.likes.all())
        self.assertIn(u2, recipe.likes.all())

    def test_like_does_not_duplicate(self):
        """Liking the same recipe twice does NOT create duplicates."""
        user = User.objects.create_user(username="@u1", email="a@a.com", password="123")
        recipe = self._create_recipe(user)

        recipe.likes.add(user)
        recipe.likes.add(user)  # attempt to duplicate

        self.assertEqual(recipe.likes.count(), 1)
