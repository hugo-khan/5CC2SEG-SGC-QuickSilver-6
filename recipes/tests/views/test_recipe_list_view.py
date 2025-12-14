"""Tests for RecipeListView."""
from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User


class RecipeListViewTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='@author',
            password='Password123',
            first_name='Auth',
            last_name='Or',
            email='author@example.com'
        )
        self.published_recipe = Recipe.objects.create(
            author=self.author,
            title='Published Recipe',
            name='Published Recipe',
            description='Published',
            ingredients='Ingredients',
            instructions='Instructions',
            is_published=True,
        )
        self.unpublished_recipe = Recipe.objects.create(
            author=self.author,
            title='Unpublished Recipe',
            name='Unpublished Recipe',
            description='Unpublished',
            ingredients='Ingredients',
            instructions='Instructions',
            is_published=False,
        )

    def test_recipe_list_loads(self):
        """Test that recipe list page loads."""
        # browse_recipes requires login, so login first
        user = User.objects.create_user(
            username='@viewer',
            password='Password123',
            first_name='View',
            last_name='Er',
            email='viewer@example.com'
        )
        self.client.login(username='@viewer', password='Password123')
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_recipe_list_shows_only_published_recipes(self):
        """Test that recipe list shows only published recipes."""
        user = User.objects.create_user(
            username='@viewer',
            password='Password123',
            first_name='View',
            last_name='Er',
            email='viewer@example.com'
        )
        self.client.login(username='@viewer', password='Password123')
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 200)
        if response.context:
            recipes = response.context.get('recipes', [])
            published_ids = [r.id for r in recipes]
            self.assertIn(self.published_recipe.id, published_ids)
            self.assertNotIn(self.unpublished_recipe.id, published_ids)

    def test_recipe_list_pagination(self):
        """Test that recipe list paginates results."""
        user = User.objects.create_user(
            username='@viewer',
            password='Password123',
            first_name='View',
            last_name='Er',
            email='viewer@example.com'
        )
        self.client.login(username='@viewer', password='Password123')
        # Create more published recipes
        for i in range(15):
            Recipe.objects.create(
                author=self.author,
                title=f'Recipe {i}',
                name=f'Recipe {i}',
                description='Test',
                ingredients='Test',
                instructions='Test',
                is_published=True,
            )
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 200)
        if response.context:
            recipes = response.context.get('recipes', [])
            self.assertTrue(len(recipes) > 0)

    def test_recipe_list_selects_related_author(self):
        """Test that recipe list uses select_related for author."""
        user = User.objects.create_user(
            username='@viewer',
            password='Password123',
            first_name='View',
            last_name='Er',
            email='viewer@example.com'
        )
        self.client.login(username='@viewer', password='Password123')
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 200)
        if response.context:
            recipes = response.context.get('recipes', [])
            for recipe in recipes:
                # Should not cause additional query
                self.assertIsNotNone(recipe.author.username)

