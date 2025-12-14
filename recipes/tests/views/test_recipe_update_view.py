from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User


class RecipeUpdateViewTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="@author",
            password="Password123",
            first_name="Auth",
            last_name="Or",
            email="author@example.com",
        )
        self.other = User.objects.create_user(
            username="@intruder",
            password="Password123",
            first_name="Other",
            last_name="User",
            email="other@example.com",
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            title="Soup",
            ingredients="Veggies",
            instructions="Cook",
        )

    def test_author_can_update_recipe(self):
        self.client.login(username="@author", password="Password123")
        response = self.client.post(
            reverse("recipe_edit", kwargs={"pk": self.recipe.pk}),
            data={
                "title": "Soup Deluxe",
                "summary": "",
                "ingredients": "Veggies",
                "instructions": "Cook longer",
                "is_published": True,
            },
            follow=True,
        )
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Soup Deluxe")
        self.assertEqual(response.status_code, 200)

    def test_non_author_cannot_update_recipe(self):
        self.client.login(username="@intruder", password="Password123")
        response = self.client.post(
            reverse("recipe_edit", kwargs={"pk": self.recipe.pk}),
            data={
                "title": "Hijacked",
                "summary": "",
                "ingredients": "Veggies",
                "instructions": "Cook",
                "is_published": True,
            },
            follow=True,
        )
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Soup")
        self.assertRedirects(
            response, reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
