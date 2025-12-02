from django.test import TestCase
from django.contrib.auth import get_user_model
from recipes.models.comment import Comment
from recipes.models.recipe import Recipe

User = get_user_model()

class CommentModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Description",
            instructions="Steps",
            user=self.user,
        )

    def test_comment_str(self):
        comment = Comment.objects.create(
            user=self.user,
            recipe=self.recipe,
            text="Great recipe!"
        )
        self.assertEqual(str(comment), "Great recipe!")