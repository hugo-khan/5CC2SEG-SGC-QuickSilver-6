from django.test import TestCase
from django.urls import reverse

from recipes.models import Follow, Recipe, User


class FeedViewTest(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username='@viewer', password='Password123', first_name='View', last_name='Er', email='viewer@example.com'
        )
        self.alice = User.objects.create_user(
            username='@alice', password='Password123', first_name='Alice', last_name='Cook', email='alice@example.com'
        )
        self.bob = User.objects.create_user(
            username='@bob', password='Password123', first_name='Bob', last_name='Chef', email='bob@example.com'
        )
        self.alice_recipe = Recipe.objects.create(
            author=self.alice,
            title='Alice Pie',
            ingredients='Stuff',
            instructions='Bake',
        )
        self.bob_recipe = Recipe.objects.create(
            author=self.bob,
            title='Bob Soup',
            ingredients='Water',
            instructions='Boil',
        )

    def test_feed_requires_login(self):
        response = self.client.get(reverse('feed'))
        self.assertEqual(response.status_code, 302)

    def test_feed_shows_only_followed_users(self):
        self.client.login(username='@viewer', password='Password123')
        Follow.objects.create(follower=self.viewer, followed=self.alice)
        response = self.client.get(reverse('feed'))
        self.assertContains(response, 'Alice Pie')
        self.assertNotContains(response, 'Bob Soup')


