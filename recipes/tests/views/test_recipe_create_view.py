from django.urls import reverse
from django.test import TestCase

from recipes.models import Recipe, User


class RecipeCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='@poster', password='Password123', first_name='Poster', last_name='One', email='poster@example.com'
        )

    def test_redirects_if_not_logged_in(self):
        response = self.client.get(reverse('recipe_create'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_authenticated_user_can_create_recipe(self):
        self.client.login(username='@poster', password='Password123')
        response = self.client.post(
            reverse('recipe_create'),
            data={
                "title": "Bread",
                "summary": "Simple bread",
                "ingredients": "Flour\nWater",
                "instructions": "Mix\nBake",
                "is_published": True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Recipe.objects.filter(title="Bread", author=self.user).exists())


