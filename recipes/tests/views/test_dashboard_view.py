"""Tests for dashboard views."""
from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User, SavedRecipe


class DashboardViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='@user',
            password='Password123',
            first_name='Test',
            last_name='User',
            email='user@example.com'
        )

    def test_dashboard_redirects_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_dashboard_loads_for_authenticated_user(self):
        """Test that dashboard loads for authenticated users."""
        self.client.login(username='@user', password='Password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_welcome.html')

    def test_dashboard_includes_user_context(self):
        """Test that dashboard includes user in context."""
        self.client.login(username='@user', password='Password123')
        response = self.client.get(reverse('dashboard'))
        self.assertIn('user', response.context)
        self.assertEqual(response.context['user'], self.user)


class BrowseRecipesViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='@user',
            password='Password123',
            first_name='Test',
            last_name='User',
            email='user@example.com'
        )
        self.author = User.objects.create_user(
            username='@author',
            password='Password123',
            first_name='Auth',
            last_name='Or',
            email='author@example.com'
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            title='Test Recipe',
            name='Test Recipe',
            description='Test description',
            ingredients='Test ingredients',
            instructions='Test instructions',
            is_published=True,
        )

    def test_browse_recipes_redirects_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_browse_recipes_loads_for_authenticated_user(self):
        """Test that browse recipes loads for authenticated users."""
        self.client.login(username='@user', password='Password123')
        response = self.client.get(reverse('recipe_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_browse_recipes_shows_all_recipes(self):
        """Test that browse recipes shows all recipes."""
        self.client.login(username='@user', password='Password123')
        response = self.client.get(reverse('recipe_list'))
        self.assertIn('recipes', response.context)
        self.assertIn(self.recipe, response.context['recipes'])

    def test_browse_recipes_shows_saved_recipe_ids(self):
        """Test that browse recipes shows saved recipe IDs."""
        self.client.login(username='@user', password='Password123')
        SavedRecipe.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.get(reverse('recipe_list'))
        self.assertIn('saved_recipe_ids', response.context)
        self.assertIn(self.recipe.id, response.context['saved_recipe_ids'])

    def test_browse_recipes_toggle_save(self):
        """Test that POST request toggles save status."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(
            reverse('recipe_list'),
            data={'recipe_id': self.recipe.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_browse_recipes_toggle_unsave(self):
        """Test that POST request toggles unsave if already saved."""
        self.client.login(username='@user', password='Password123')
        SavedRecipe.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.post(
            reverse('recipe_list'),
            data={'recipe_id': self.recipe.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())

