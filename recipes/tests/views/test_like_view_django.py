"""Tests for ToggleLikeView using Django TestCase."""
from django.test import TestCase
from django.urls import reverse
from recipes.models import Like, Recipe, User


class ToggleLikeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='@testuser',
            email='test@example.com',
            password='password123'
        )
        self.author = User.objects.create_user(
            username='@author',
            email='author@example.com',
            password='password123'
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            title='Test Recipe',
            name='Test Recipe',
            description='A simple test recipe.',
            ingredients='Test ingredients',
            instructions='Test instructions',
            is_published=True
        )

    def test_authenticated_user_can_like_recipe(self):
        """Test that authenticated user can like a recipe."""
        self.client.login(username='@testuser', password='password123')
        url = reverse('toggle_like', kwargs={'recipe_id': self.recipe.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Like.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_authenticated_user_can_unlike_recipe(self):
        """Test that authenticated user can unlike a recipe."""
        Like.objects.create(user=self.user, recipe=self.recipe)
        self.client.login(username='@testuser', password='password123')
        url = reverse('toggle_like', kwargs={'recipe_id': self.recipe.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Like.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_unauthenticated_user_redirected(self):
        """Test that unauthenticated users are redirected to login."""
        url = reverse('toggle_like', kwargs={'recipe_id': self.recipe.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/log_in', response.url)
        self.assertEqual(Like.objects.count(), 0)

    def test_liking_twice_toggles_like(self):
        """Test that liking twice toggles the like."""
        self.client.login(username='@testuser', password='password123')
        url = reverse('toggle_like', kwargs={'recipe_id': self.recipe.id})
        
        # First click: like
        self.client.post(url)
        self.assertTrue(Like.objects.filter(user=self.user, recipe=self.recipe).exists())
        
        # Second click: unlike
        self.client.post(url)
        self.assertFalse(Like.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_redirect_back_to_recipe_page(self):
        """Test that view redirects back to recipe detail page."""
        self.client.login(username='@testuser', password='password123')
        url = reverse('toggle_like', kwargs={'recipe_id': self.recipe.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('recipe_detail', kwargs={'pk': self.recipe.id}))

    def test_nonexistent_recipe_returns_404(self):
        """Test that nonexistent recipe returns 404."""
        self.client.login(username='@testuser', password='password123')
        url = reverse('toggle_like', kwargs={'recipe_id': 99999})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

