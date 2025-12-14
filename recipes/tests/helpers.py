from django.test import TestCase
from django.urls import reverse
from with_asserts.mixin import AssertHTMLMixin

from recipes.helpers import collect_all_ingredients
from recipes.models import Recipe, User


def reverse_with_next(url_name, next_url):
    """Extended version of reverse to generate URLs with redirects"""
    url = reverse(url_name)
    url += f"?next={next_url}"
    return url


class LogInTester:
    """Class support login in tests."""

    def _is_logged_in(self):
        """Returns True if a user is logged in.  False otherwise."""

        return "_auth_user_id" in self.client.session.keys()


class MenuTesterMixin(AssertHTMLMixin):
    """Class to extend tests with tools to check the presents of menu items."""

    menu_urls = [reverse("profile"), reverse("log_out")]

    def assert_menu(self, response):
        """Check that menu is present."""

        for url in self.menu_urls:
            with self.assertHTML(response, f'a[href="{url}"]'):
                pass

    def assert_no_menu(self, response):
        """Check that no menu is present."""

        for url in self.menu_urls:
            self.assertNotHTML(response, f'a[href="{url}"]')


class TestCollectAllIngredients(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="password")
        # Recipe with comma-separated ingredients
        Recipe.objects.create(
            title="Cake",
            description="Tasty cake",
            ingredients="flour, sugar, eggs",
            instructions="Mix and bake",
            author=self.user,
            is_published=True,
        )
        Recipe.objects.create(
            title="Pancakes",
            description="Breakfast pancakes",
            ingredients="milk, eggs, flour",
            instructions="Mix and fry",
            author=self.user,
            is_published=True,
        )

    def test_collect_all_ingredients_returns_unique_list(self):
        ingredients = collect_all_ingredients()
        # Should include all ingredients from both recipes, no duplicates
        expected = ["flour", "sugar", "eggs", "milk"]
        self.assertCountEqual(ingredients, expected)

    def test_collect_all_ingredients_strips_whitespace(self):
        Recipe.objects.create(
            title="Salad",
            description="Fresh salad",
            ingredients=" lettuce , tomato , cucumber ",
            instructions="Mix together",
            author=self.user,
            is_published=True,
        )
        ingredients = collect_all_ingredients()
        self.assertIn("lettuce", ingredients)
        self.assertIn("tomato", ingredients)
        self.assertIn("cucumber", ingredients)
