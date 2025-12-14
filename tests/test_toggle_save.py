from django.test import TestCase, Client
from django.urls import reverse
from recipes.models import Recipe, User
from recipes.models.saved_recipes import SavedRecipe



class ToggleSaveTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="john", password="pass1234")
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Title",
            summary="Summary",
            ingredients="Eggs, Milk",
            instructions="Do this",
            name="Test Name",
            description="Desc"
        )

    def test_toggle_save_creates(self):
        self.client.login(username="john", password="pass1234")
        url = reverse("toggle_save_recipe", args=[self.recipe.id])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SavedRecipe.objects.filter(user=self.user, recipe=self.recipe).exists())
