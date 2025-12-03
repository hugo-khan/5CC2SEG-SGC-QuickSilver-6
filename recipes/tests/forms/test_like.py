import pytest
from django.urls import reverse
from recipes.models.user import User
from recipes.models.recipe import Recipe


@pytest.mark.django_db
class TestToggleLikeView:

    def setup_method(self):
        self.user = User.objects.create_user(
            username="@testuser",
            email="test@example.com",
            password="password123"
        )
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="A simple test recipe."
        )

    def test_user_can_like_recipe(self, client):
        """User can like a recipe."""
        client.login(username="@testuser", password="password123")
        url = reverse("toggle_like", args=[self.recipe.id])

        response = client.post(url)

        # Assertions
        assert response.status_code == 302   # should redirect back
        assert self.user in self.recipe.likes.all()

    def test_user_can_unlike_recipe(self, client):
        """User can unlike liked recipe"""
        self.recipe.likes.add(self.user)
        client.login(username="@testuser", password="password123")
        url = reverse("toggle_like", args=[self.recipe.id])

        response = client.post(url)

        # Assertions
        assert response.status_code == 302
        assert self.user not in self.recipe.likes.all()

    def test_unauthenticated_user_cannot_like(self, client):
        """Guests can't like a recipe."""
        url = reverse("toggle_like", args=[self.recipe.id])

        response = client.post(url)


        assert response.status_code in (302, 301)
        assert self.recipe.likes.count() == 0

    def test_like_does_not_create_duplicates(self, client):
        """Repeated liking shouldn't create multiple likes"""
        client.login(username="@testuser", password="password123")
        url = reverse("toggle_like", args=[self.recipe.id])

        # Like twice check
        client.post(url)
        client.post(url)


        assert self.recipe.likes.count() == 0
