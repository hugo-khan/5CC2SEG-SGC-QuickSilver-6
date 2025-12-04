"""Tests for recipe_search view."""
from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User


class RecipeSearchViewTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='@author',
            password='Password123',
            first_name='Auth',
            last_name='Or',
            email='author@example.com'
        )
        self.recipe1 = Recipe.objects.create(
            author=self.author,
            title='Pasta Recipe',
            name='Pasta Recipe',
            description='Delicious pasta',
            ingredients='Pasta, sauce',
            instructions='Cook pasta',
            dietary_requirement='vegetarian',
            is_published=True,
        )
        self.recipe2 = Recipe.objects.create(
            author=self.author,
            title='Chicken Recipe',
            name='Chicken Recipe',
            description='Tasty chicken',
            ingredients='Chicken, spices',
            instructions='Cook chicken',
            dietary_requirement='none',
            is_published=True,
        )

    def test_recipe_search_loads(self):
        """Test that recipe search page loads."""
        response = self.client.get(reverse('recipe_search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes_search.html')

    def test_recipe_search_shows_all_recipes(self):
        """Test that recipe search shows all recipes by default."""
        response = self.client.get(reverse('recipe_search'))
        self.assertIn('recipes', response.context)
        self.assertEqual(len(response.context['recipes']), 2)

    def test_recipe_search_filters_by_name(self):
        """Test that recipe search filters by recipe name."""
        response = self.client.get(reverse('recipe_search') + '?search=Pasta')
        self.assertIn('recipes', response.context)
        recipes = response.context['recipes']
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].name, 'Pasta Recipe')

    def test_recipe_search_filters_by_description(self):
        """Test that recipe search filters by description."""
        response = self.client.get(reverse('recipe_search') + '?search=Delicious')
        self.assertIn('recipes', response.context)
        recipes = response.context['recipes']
        self.assertEqual(len(recipes), 1)
        self.assertIn('Delicious', recipes[0].description)

    def test_recipe_search_filters_by_dietary_requirement(self):
        """Test that recipe search filters by dietary requirement."""
        response = self.client.get(reverse('recipe_search') + '?dietary_requirement=vegetarian')
        self.assertIn('recipes', response.context)
        recipes = response.context['recipes']
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].dietary_requirement, 'vegetarian')

    def test_recipe_search_sorts_by_date(self):
        """Test that recipe search sorts by date."""
        response = self.client.get(reverse('recipe_search') + '?sort_by=date')
        self.assertIn('recipes', response.context)
        recipes = list(response.context['recipes'])
        # Should be sorted newest first
        self.assertEqual(recipes[0].id, self.recipe2.id)

    def test_recipe_search_sorts_by_popularity(self):
        """Test that recipe search sorts by popularity."""
        self.recipe1.popularity = 10
        self.recipe1.save()
        self.recipe2.popularity = 5
        self.recipe2.save()
        response = self.client.get(reverse('recipe_search') + '?sort_by=popularity')
        self.assertIn('recipes', response.context)
        recipes = list(response.context['recipes'])
        self.assertEqual(recipes[0].popularity, 10)

    def test_recipe_search_sorts_by_name(self):
        """Test that recipe search sorts by name."""
        response = self.client.get(reverse('recipe_search') + '?sort_by=name')
        self.assertIn('recipes', response.context)
        recipes = list(response.context['recipes'])
        # Should be sorted alphabetically
        self.assertTrue(recipes[0].name <= recipes[1].name)

    def test_recipe_search_pagination(self):
        """Test that recipe search paginates results."""
        # Create more recipes
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
        response = self.client.get(reverse('recipe_search'))
        self.assertIn('page_obj', response.context)
        self.assertTrue(response.context['page_obj'].has_other_pages())

    def test_recipe_search_includes_form(self):
        """Test that recipe search includes filter form."""
        response = self.client.get(reverse('recipe_search'))
        self.assertIn('form', response.context)

