from django.test import TestCase
from django.urls import reverse

from recipes.models import Follow, User


class FollowViewsTest(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username='@alice', password='Password123', first_name='Alice', last_name='Cook', email='alice@example.com'
        )
        self.bob = User.objects.create_user(
            username='@bob', password='Password123', first_name='Bob', last_name='Chef', email='bob@example.com'
        )

    def test_follow_creates_relationship(self):
        self.client.login(username='@alice', password='Password123')
        response = self.client.post(reverse('follow_user', kwargs={'user_id': self.bob.pk}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Follow.objects.filter(follower=self.alice, followed=self.bob).exists())

    def test_unfollow_removes_relationship(self):
        Follow.objects.create(follower=self.alice, followed=self.bob)
        self.client.login(username='@alice', password='Password123')
        self.client.post(reverse('unfollow_user', kwargs={'user_id': self.bob.pk}), follow=True)
        self.assertFalse(Follow.objects.filter(follower=self.alice, followed=self.bob).exists())


