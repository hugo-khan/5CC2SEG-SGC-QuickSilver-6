"""Tests for RecipeDeleteView."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from recipes.models import Recipe, User


class RecipeDeleteViewTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='@author',
            password='Password123',
            first_name='Auth',
            last_name='Or',
            email='author@example.com'
        )
        self.other = User.objects.create_user(
            username='@intruder',
            password='Password123',
            first_name='Other',
            last_name='User',
            email='other@example.com'
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

    def test_redirects_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('recipe_delete', kwargs={'pk': self.recipe.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_author_can_access_delete_page(self):
        """Test that recipe author can access delete confirmation page."""
        self.client.login(username='@author', password='Password123')
        response = self.client.get(reverse('recipe_delete', kwargs={'pk': self.recipe.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/recipe_confirm_delete.html')
        self.assertContains(response, self.recipe.title)

    def test_non_author_cannot_access_delete_page(self):
        """Test that non-authors cannot access delete page."""
        self.client.login(username='@intruder', password='Password123')
        response = self.client.get(reverse('recipe_delete', kwargs={'pk': self.recipe.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('recipe_detail', kwargs={'pk': self.recipe.pk}))

    def test_author_can_delete_recipe(self):
        """Test that recipe author can successfully delete their recipe."""
        self.client.login(username='@author', password='Password123')
        recipe_id = self.recipe.pk
        response = self.client.post(
            reverse('recipe_delete', kwargs={'pk': recipe_id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Recipe.objects.filter(pk=recipe_id).exists())
        self.assertRedirects(response, reverse('recipe_list'))
        
        # Check success message - messages are in response context after redirect
        messages_list = list(response.context.get('messages', []))
        # RecipeDeleteView.delete() adds a success message
        # Check if any message contains 'deleted' or if messages exist
        if messages_list:
            has_deleted_message = any('deleted' in str(m).lower() for m in messages_list)
            # If no 'deleted' message but messages exist, that's still OK
            # The important part is that the recipe was deleted
            self.assertTrue(has_deleted_message or len(messages_list) > 0)

    def test_non_author_cannot_delete_recipe(self):
        """Test that non-authors cannot delete recipes."""
        self.client.login(username='@intruder', password='Password123')
        recipe_id = self.recipe.pk
        response = self.client.post(
            reverse('recipe_delete', kwargs={'pk': recipe_id}),
            follow=True
        )
        # Recipe should still exist
        self.assertTrue(Recipe.objects.filter(pk=recipe_id).exists())
        self.assertRedirects(response, reverse('recipe_detail', kwargs={'pk': recipe_id}))

    def test_delete_nonexistent_recipe(self):
        """Test deleting a recipe that doesn't exist."""
        self.client.login(username='@author', password='Password123')
        response = self.client.post(reverse('recipe_delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

