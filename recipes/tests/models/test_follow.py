from django.db import IntegrityError
from django.test import TestCase

from recipes.models import Follow, User


class FollowModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username='@alice', password='Password123', first_name='Alice', last_name='Doe', email='alice@example.com'
        )
        cls.bob = User.objects.create_user(
            username='@bob', password='Password123', first_name='Bob', last_name='Smith', email='bob@example.com'
        )

    def test_user_cannot_follow_twice(self):
        Follow.objects.create(follower=self.alice, followed=self.bob)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.alice, followed=self.bob)

    def test_string_representation(self):
        relation = Follow.objects.create(follower=self.alice, followed=self.bob)
        self.assertIn('@alice', str(relation))
        self.assertIn('@bob', str(relation))


