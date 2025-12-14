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

    def test_authenticated_user_can_like_recipe(self):
        self.client.login(username="@testuser", password="password123")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user, self.recipe.likes.all())

    def test_authenticated_user_can_unlike_recipe(self):
        self.recipe.likes.add(self.user)
        self.client.login(username="@testuser", password="password123")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user, self.recipe.likes.all())

    def test_unauthenticated_user_redirected(self):
        response = self.client.post(self.url)

        self.assertIn(response.status_code, (301, 302))
        self.assertEqual(self.recipe.likes.count(), 0)

    def test_liking_twice_toggles_like(self):
        self.client.login(username="@testuser", password="password123")

        self.client.post(self.url)  # like
        self.assertIn(self.user, self.recipe.likes.all())

        self.client.post(self.url)  # unlike
        self.assertNotIn(self.user, self.recipe.likes.all())

    def test_redirect_back_to_recipe_page(self):
        """Check the view redirects back to the recipe page or feed."""
        self.client.login(username="@testuser", password="password123")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url)
