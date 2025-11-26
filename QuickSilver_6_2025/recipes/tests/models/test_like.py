import pytest
from recipes.models.user import User
from recipes.models.recipe import Recipe


@pytest.mark.django_db
class TestLikeModel:

    def test_recipe_has_likes_field(self):
        """Ensure Recipe model contains a ManyToManyField named 'likes'."""
        recipe = Recipe()
        assert hasattr(recipe, "likes")

    def test_user_can_like_recipe(self):
        """User should be able to like a recipe."""
        user = User.objects.create_user(
            username="@u1", email="u1@example.com", password="pass123"
        )
        recipe = Recipe.objects.create(title="Test", description="test")

        recipe.likes.add(user)

        assert user in recipe.likes.all()
        assert recipe.likes.count() == 1

    def test_user_can_unlike_recipe(self):
        """User can remove a like from a recipe."""
        user = User.objects.create_user(
            username="@u1", email="u1@example.com", password="pass123"
        )
        recipe = Recipe.objects.create(title="Test", description="test")

        recipe.likes.add(user)
        recipe.likes.remove(user)

        assert user not in recipe.likes.all()
        assert recipe.likes.count() == 0

    def test_multiple_users_can_like_same_recipe(self):
        """More than one user may like a recipe."""
        u1 = User.objects.create_user(username="@u1", email="a@a.com", password="123")
        u2 = User.objects.create_user(username="@u2", email="b@b.com", password="123")

        recipe = Recipe.objects.create(title="Test", description="test")

        recipe.likes.add(u1)
        recipe.likes.add(u2)

        assert recipe.likes.count() == 2
        assert u1 in recipe.likes.all()
        assert u2 in recipe.likes.all()

    def test_like_does_not_duplicate(self):
        """Liking the same recipe twice does NOT create duplicates."""
        user = User.objects.create_user(username="@u1", email="a@a.com", password="123")
        recipe = Recipe.objects.create(title="Test", description="test")

        recipe.likes.add(user)
        recipe.likes.add(user)  # attempt to duplicate

        assert recipe.likes.count() == 1
