"""Tests for author_recipes view."""

from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User


class AuthorRecipesViewTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="@author",
            password="Password123",
            first_name="Auth",
            last_name="Or",
            email="author@example.com",
        )
        self.other_author = User.objects.create_user(
            username="@other",
            password="Password123",
            first_name="Other",
            last_name="Author",
            email="other@example.com",
        )
        self.recipe1 = Recipe.objects.create(
            author=self.author,
            title="Recipe 1",
            name="Recipe 1",
            description="First recipe",
            ingredients="Ingredients 1",
            instructions="Instructions 1",
            is_published=True,
        )
        self.recipe2 = Recipe.objects.create(
            author=self.author,
            title="Recipe 2",
            name="Recipe 2",
            description="Second recipe",
            ingredients="Ingredients 2",
            instructions="Instructions 2",
            is_published=True,
        )
        self.recipe3 = Recipe.objects.create(
            author=self.other_author,
            title="Other Recipe",
            name="Other Recipe",
            description="Other author recipe",
            ingredients="Ingredients",
            instructions="Instructions",
            is_published=True,
        )

    def test_author_recipes_loads(self):
        """Test that author recipes page loads."""
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "author_recipes.html")

    def test_author_recipes_shows_only_author_recipes(self):
        """Test that author recipes shows only recipes by that author."""
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
        )
        self.assertIn("recipes", response.context)
        recipes = response.context["recipes"]
        self.assertEqual(len(recipes), 2)
        for recipe in recipes:
            self.assertEqual(recipe.author, self.author)

    def test_author_recipes_includes_author_info(self):
        """Test that author recipes includes author in context."""
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
        )
        self.assertIn("author", response.context)
        self.assertEqual(response.context["author"], self.author)

    def test_author_recipes_filters_by_search(self):
        """Test that author recipes can be filtered by search."""
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
            + "?search=First"
        )
        self.assertIn("recipes", response.context)
        recipes = response.context["recipes"]
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].name, "Recipe 1")

    def test_author_recipes_filters_by_dietary_requirement(self):
        """Test that author recipes can be filtered by dietary requirement."""
        self.recipe1.dietary_requirement = "vegan"
        self.recipe1.save()
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
            + "?dietary_requirement=vegan"
        )
        self.assertIn("recipes", response.context)
        recipes = response.context["recipes"]
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].dietary_requirement, "vegan")

    def test_author_recipes_sorts_correctly(self):
        """Test that author recipes can be sorted."""
        self.recipe1.popularity = 5
        self.recipe1.save()
        self.recipe2.popularity = 10
        self.recipe2.save()
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
            + "?sort_by=popularity"
        )
        self.assertIn("recipes", response.context)
        recipes = list(response.context["recipes"])
        self.assertEqual(recipes[0].popularity, 10)

    def test_author_recipes_with_nonexistent_author(self):
        """Test that author recipes returns 404 for nonexistent author."""
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_author_recipes_pagination(self):
        """Test that author recipes paginates results."""
        # Create more recipes
        for i in range(15):
            Recipe.objects.create(
                author=self.author,
                title=f"Recipe {i}",
                name=f"Recipe {i}",
                description="Test",
                ingredients="Test",
                instructions="Test",
                is_published=True,
            )
        response = self.client.get(
            reverse("author_recipes", kwargs={"author_id": self.author.id})
        )
        self.assertIn("page_obj", response.context)
        self.assertTrue(response.context["page_obj"].has_other_pages())
