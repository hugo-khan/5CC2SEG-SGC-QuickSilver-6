from django.test import TestCase

from recipes.models import Recipe, User


class RecipeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='@cook', password='Password123', first_name='Test', last_name='Cook', email='cook@example.com'
        )

    def test_string_representation(self):
        recipe = Recipe.objects.create(
            author=self.user,
            title='Tomato Soup',
            ingredients='Tomatoes\nWater',
            instructions='Mix\nBoil',
        )
        self.assertEqual(str(recipe), 'Tomato Soup')

    def test_total_time_minutes(self):
        recipe = Recipe.objects.create(
            author=self.user,
            title='Pasta',
            ingredients='Pasta',
            instructions='Cook it',
            prep_time_minutes=5,
            cook_time_minutes=10,
        )
        self.assertEqual(recipe.total_time_minutes, 15)


