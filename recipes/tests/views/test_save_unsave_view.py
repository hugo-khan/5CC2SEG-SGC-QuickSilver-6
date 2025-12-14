"""Tests for toggle_save_recipe view."""
from django.test import TestCase
from django.urls import reverse
import json

from recipes.models import Recipe, User, SavedRecipe


class ToggleSaveRecipeViewTest(TestCase):
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

    def test_toggle_save_redirects_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'pk': self.recipe.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_toggle_save_creates_saved_recipe(self):
        """Test that POST request creates a saved recipe."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(
            reverse('toggle_save_recipe', kwargs={'pk': self.recipe.id}),
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.id})
        )
        # The view redirects, not returns JSON
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_toggle_save_deletes_saved_recipe(self):
        """Test that POST request deletes saved recipe if it exists."""
        self.client.login(username='@user', password='Password123')
        SavedRecipe.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.post(
            reverse('toggle_save_recipe', kwargs={'pk': self.recipe.id}),
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.id})
        )
        # The view redirects, not returns JSON
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_toggle_save_redirects(self):
        """Test that response redirects back to referer or recipe detail."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(
            reverse('toggle_save_recipe', kwargs={'pk': self.recipe.id}),
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.id})
        )
        # Should redirect
        self.assertEqual(response.status_code, 302)
        # Should redirect to referer or recipe detail
        self.assertTrue(
            response.url == reverse('recipe_detail', kwargs={'pk': self.recipe.id}) or
            self.recipe.title in str(response.url)
        )

    def test_toggle_save_with_nonexistent_recipe(self):
        """Test that toggle save returns 404 for nonexistent recipe."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

