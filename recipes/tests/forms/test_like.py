from django.test import TestCase
from django.urls import reverse

from recipes.models import User, Recipe


class TestToggleLikeView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="@testuser",
            email="test@example.com",
            password="password123",
        )
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            name="Test Recipe",
            description="A simple test recipe.",
            ingredients="a,b",
            instructions="mix",
            is_published=True,
        )
        self.url = reverse("toggle_like", args=[self.recipe.id])

    def test_user_can_like_recipe(self):
        """Authenticated user can like a recipe."""
        self.client.login(username="@testuser", password="password123")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user, self.recipe.likes.all())

    def test_user_can_unlike_recipe(self):
        """Authenticated user can unlike a recipe they've liked."""
        self.recipe.likes.add(self.user)
        self.client.login(username="@testuser", password="password123")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user, self.recipe.likes.all())

    def test_unauthenticated_user_cannot_like(self):
        """Guests can't like a recipe."""
        response = self.client.post(self.url)

        self.assertIn(response.status_code, (301, 302))
        self.assertEqual(self.recipe.likes.count(), 0)

    def test_like_toggle_prevents_duplicates(self):
        """Toggling twice should unlike and leave zero likes."""
        self.client.login(username="@testuser", password="password123")

        self.client.post(self.url)  # like
        self.client.post(self.url)  # unlike

        self.assertEqual(self.recipe.likes.count(), 0)
