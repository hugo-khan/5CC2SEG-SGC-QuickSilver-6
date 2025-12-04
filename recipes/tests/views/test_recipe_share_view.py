"""Tests for RecipeShareView."""
from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User


class RecipeShareViewTest(TestCase):
    def setUp(self):
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

    def test_share_view_loads_for_published_recipe(self):
        """Test that share view loads for published recipes."""
        response = self.client.get(
            reverse('recipe_share', kwargs={'share_token': self.recipe.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/recipe_share.html')
        self.assertContains(response, self.recipe.title)

    def test_share_view_not_accessible_for_unpublished_recipe(self):
        """Test that share view is not accessible for unpublished recipes."""
        self.recipe.is_published = False
        self.recipe.save()
        response = self.client.get(
            reverse('recipe_share', kwargs={'share_token': self.recipe.share_token})
        )
        self.assertEqual(response.status_code, 404)

    def test_share_view_works_without_login(self):
        """Test that share view works for unauthenticated users."""
        self.client.logout()
        response = self.client.get(
            reverse('recipe_share', kwargs={'share_token': self.recipe.share_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe.title)

    def test_share_view_includes_share_url(self):
        """Test that share view includes share URL in context."""
        response = self.client.get(
            reverse('recipe_share', kwargs={'share_token': self.recipe.share_token})
        )
        self.assertIn('share_url', response.context)
        self.assertIn('is_shared_view', response.context)
        self.assertTrue(response.context['is_shared_view'])

    def test_share_view_with_invalid_token(self):
        """Test that share view returns 404 for invalid token."""
        import uuid
        invalid_token = uuid.uuid4()
        response = self.client.get(
            reverse('recipe_share', kwargs={'share_token': invalid_token})
        )
        self.assertEqual(response.status_code, 404)

