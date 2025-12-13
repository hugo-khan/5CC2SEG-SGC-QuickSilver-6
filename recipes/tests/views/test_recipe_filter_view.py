from django.test import TestCase, Client
from django.urls import reverse
from recipes.models import Recipe, User


class TestRecipeFilterView(TestCase):
    fixtures = ['other_users.json', 'sample_comment_data.json', 'recipes.json']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.force_login(self.user)

    def test_feed_filter_by_ingredient_single(self):
        ingredient = 'Flour'
        url = reverse('feed')
        response = self.client.get(url, {'ingredients': [ingredient]})
        self.assertEqual(response.status_code, 200)
        for recipe in response.context['recipes']:
            self.assertIn(ingredient.lower(), recipe.ingredients.lower())

    def test_feed_filter_by_ingredient_multiple(self):
        ingredients = ['Flour', 'Sugar']
        url = reverse('feed')
        response = self.client.get(url, {'ingredients': ingredients})
        self.assertEqual(response.status_code, 200)
        for recipe in response.context['recipes']:
            for ing in ingredients:
                self.assertIn(ing.lower(), recipe.ingredients.lower())

    def test_recipe_list_filter_by_ingredient(self):
        ingredient = 'Flour'
        url = reverse('recipe_list')
        response = self.client.get(url, {'ingredients': [ingredient]})
        self.assertEqual(response.status_code, 200)
        for recipe in response.context['recipes']:
            self.assertIn(ingredient.lower(), recipe.ingredients.lower())
