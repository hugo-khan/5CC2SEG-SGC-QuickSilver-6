import pytest
from django.urls import reverse
from recipes.models.user import User
from recipes.models.recipe import recipe


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
        self.url = reverse("toggle_like", args=[self.recipe.id])

    def test_authenticated_user_can_like_recipe(self, client):
        client.login(username="@testuser", password="password123")

        response = client.post(self.url)

        assert response.status_code == 302
        assert self.user in self.recipe.likes.all()

    def test_authenticated_user_can_unlike_recipe(self, client):
        self.recipe.likes.add(self.user)
        client.login(username="@testuser", password="password123")

        response = client.post(self.url)

        assert response.status_code == 302
        assert self.user not in self.recipe.likes.all()

    def test_unauthenticated_user_redirected(self, client):
        response = client.post(self.url)

        # Should redirect to login page
        assert response.status_code in (301, 302)
        assert self.recipe.likes.count() == 0

    def test_liking_twice_toggles_like(self, client):
        client.login(username="@testuser", password="password123")

        # First click: like
        client.post(self.url)
        assert self.user in self.recipe.likes.all()

        # Second click: unlike
        client.post(self.url)
        assert self.user not in self.recipe.likes.all()

    def test_redirect_back_to_recipe_page(self, client):
        """Check the view redirects back to the recipe page or feed."""
        client.login(username="@testuser", password="password123")

        response = client.post(self.url)

        assert response.status_code == 302
        assert response.url is not None  # Should redirect to a real page
