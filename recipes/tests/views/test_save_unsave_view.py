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
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'recipe_id': self.recipe.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_toggle_save_creates_saved_recipe(self):
        """Test that POST request creates a saved recipe."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'recipe_id': self.recipe.id}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['is_saved'])
        self.assertTrue(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_toggle_save_deletes_saved_recipe(self):
        """Test that POST request deletes saved recipe if it exists."""
        self.client.login(username='@user', password='Password123')
        SavedRecipe.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'recipe_id': self.recipe.id}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['is_saved'])
        self.assertFalse(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_toggle_save_returns_json(self):
        """Test that response is JSON format."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'recipe_id': self.recipe.id}))
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content)
        self.assertIn('is_saved', data)

    def test_toggle_save_with_nonexistent_recipe(self):
        """Test that toggle save returns 404 for nonexistent recipe."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(reverse('toggle_save_recipe', kwargs={'recipe_id': 99999}))
        self.assertEqual(response.status_code, 404)

