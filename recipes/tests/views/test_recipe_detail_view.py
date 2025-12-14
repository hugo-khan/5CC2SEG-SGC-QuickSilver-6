"""Tests for RecipeDetailView."""

from django.test import TestCase
from django.urls import reverse

from recipes.models import Comment, Follow, Like, Recipe, SavedRecipe, User


class RecipeDetailViewTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="@author",
            password="Password123",
            first_name="Auth",
            last_name="Or",
            email="author@example.com",
        )
        self.viewer = User.objects.create_user(
            username="@viewer",
            password="Password123",
            first_name="View",
            last_name="Er",
            email="viewer@example.com",
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe",
            name="Test Recipe",
            description="Test description",
            ingredients="Test ingredients",
            instructions="Test instructions",
            is_published=True,
        )

    def test_recipe_detail_page_loads(self):
        """Test that recipe detail page loads successfully."""
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipes/recipe_detail.html")
        self.assertContains(response, self.recipe.title)

    def test_recipe_detail_shows_recipe_info(self):
        """Test that recipe detail shows all recipe information."""
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertContains(response, self.recipe.title)
        self.assertContains(response, self.recipe.ingredients)
        self.assertContains(response, self.recipe.instructions)

    def test_recipe_detail_shows_author_info(self):
        """Test that recipe detail shows author information."""
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertContains(response, self.author.username)

    def test_recipe_detail_shows_share_url(self):
        """Test that recipe detail includes share URL in context."""
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertIn("share_url", response.context)
        self.assertIsNotNone(response.context["share_url"])

    def test_recipe_detail_shows_like_count(self):
        """Test that recipe detail shows like count."""
        # Add a like
        Like.objects.create(user=self.viewer, recipe=self.recipe)
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertIn("total_likes", response.context)
        self.assertEqual(response.context["total_likes"], 1)

    def test_recipe_detail_shows_has_liked_for_authenticated_user(self):
        """Test that recipe detail shows if user has liked the recipe."""
        self.client.login(username="@viewer", password="Password123")
        Like.objects.create(user=self.viewer, recipe=self.recipe)
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertIn("has_liked", response.context)
        self.assertTrue(response.context["has_liked"])

    def test_recipe_detail_shows_is_favourited(self):
        """Test that recipe detail shows if recipe is saved."""
        self.client.login(username="@viewer", password="Password123")
        SavedRecipe.objects.create(user=self.viewer, recipe=self.recipe)
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertIn("is_favourited", response.context)
        self.assertTrue(response.context["is_favourited"])

    def test_recipe_detail_shows_follow_status(self):
        """Test that recipe detail shows follow status for author."""
        self.client.login(username="@viewer", password="Password123")
        Follow.objects.create(follower=self.viewer, followed=self.author)
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertIn("is_following_author", response.context)
        self.assertTrue(response.context["is_following_author"])

    def test_recipe_detail_shows_comments(self):
        """Test that recipe detail shows comments."""
        comment = Comment.objects.create(
            user=self.viewer, recipe=self.recipe, text="Test comment"
        )
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertIn("comments", response.context)
        self.assertIn(comment, response.context["comments"])

    def test_recipe_detail_shows_edit_button_for_author(self):
        """Test that edit button is shown for recipe author."""
        self.client.login(username="@author", password="Password123")
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertContains(response, "Edit Recipe")
        self.assertContains(
            response, reverse("recipe_edit", kwargs={"pk": self.recipe.pk})
        )

    def test_recipe_detail_shows_delete_button_for_author(self):
        """Test that delete button is shown for recipe author."""
        self.client.login(username="@author", password="Password123")
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertContains(response, "Delete Recipe")
        self.assertContains(
            response, reverse("recipe_delete", kwargs={"pk": self.recipe.pk})
        )

    def test_recipe_detail_shows_follow_button_for_non_author(self):
        """Test that follow button is shown for non-authors."""
        self.client.login(username="@viewer", password="Password123")
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertContains(response, "Follow")

    def test_recipe_detail_with_image_url(self):
        """Test that recipe detail displays image if image_url is set."""
        self.recipe.image_url = "https://example.com/image.jpg"
        self.recipe.save()
        response = self.client.get(
            reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        self.assertContains(response, "https://example.com/image.jpg")
