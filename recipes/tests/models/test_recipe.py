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

    def test_total_time_minutes_uses_cooking_time(self):
        """Test that total_time_minutes prefers cooking_time over prep+cook."""
        recipe = Recipe.objects.create(
            author=self.user,
            title='Pasta',
            ingredients='Pasta',
            instructions='Cook it',
            prep_time_minutes=5,
            cook_time_minutes=10,
            cooking_time=20,
        )
        self.assertEqual(recipe.total_time_minutes, 20)

    def test_get_share_url(self):
        """Test that get_share_url generates correct share URL."""
        recipe = Recipe.objects.create(
            author=self.user,
            title='Test Recipe',
            name='Test Recipe',
            description='Test',
            ingredients='Test',
            instructions='Test',
        )
        # Create a mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        share_url = recipe.get_share_url(request)
        self.assertIn(str(recipe.share_token), share_url)
        self.assertIn('share', share_url)

    def test_recipe_has_share_token(self):
        """Test that recipe automatically gets a share_token."""
        recipe = Recipe.objects.create(
            author=self.user,
            title='Test Recipe',
            name='Test Recipe',
            description='Test',
            ingredients='Test',
            instructions='Test',
        )
        self.assertIsNotNone(recipe.share_token)

    def test_recipe_share_token_is_unique(self):
        """Test that each recipe has a unique share_token."""
        recipe1 = Recipe.objects.create(
            author=self.user,
            title='Recipe 1',
            name='Recipe 1',
            description='Test',
            ingredients='Test',
            instructions='Test',
        )
        recipe2 = Recipe.objects.create(
            author=self.user,
            title='Recipe 2',
            name='Recipe 2',
            description='Test',
            ingredients='Test',
            instructions='Test',
        )
        self.assertNotEqual(recipe1.share_token, recipe2.share_token)

    def test_recipe_image_url_field(self):
        """Test that recipe can have an image_url."""
        recipe = Recipe.objects.create(
            author=self.user,
            title='Test Recipe',
            name='Test Recipe',
            description='Test',
            ingredients='Test',
            instructions='Test',
            image_url='https://example.com/image.jpg',
        )
        self.assertEqual(recipe.image_url, 'https://example.com/image.jpg')

    def test_recipe_created_by_property(self):
        """Test that created_by property returns author."""
        recipe = Recipe.objects.create(
            author=self.user,
            title='Test Recipe',
            name='Test Recipe',
            description='Test',
            ingredients='Test',
            instructions='Test',
        )
        self.assertEqual(recipe.created_by, self.user)
