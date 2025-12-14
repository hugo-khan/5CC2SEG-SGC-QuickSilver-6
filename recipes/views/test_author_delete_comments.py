from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from recipes.models import Comment, Recipe


class CommentDeleteViewTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(username="author", password="pass123")
        self.other_user = User.objects.create_user(
            username="otheruser", password="pass123"
        )

        # Recipe
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="test",
            instructions="mix",
            ingredients="a,b",
            prep_time_minutes=5,
            cook_time_minutes=5,
            servings=1,
            is_published=True,
            author=self.author,
        )
        self.comment = Comment.objects.create(
            user=self.author, recipe=self.recipe, content="Nice recipe!"
        )

        self.url = reverse("comment_delete", kwargs={"pk": self.comment.pk})
        self.recipe_url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})

    def test_get_delete_page_author_only(self):
        self.client.login(username="author", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipes/comment_confirm_delete.html")
        self.assertEqual(response.context["object"], self.comment)

    def test_get_delete_page_denied_for_non_author(self):
        self.client.login(username="otheruser", password="pass123")
        response = self.client.get(self.url)
        self.assertRedirects(response, self.recipe_url)
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("You do not have permission to delete this comment.", messages)

    def test_author_can_delete_comment(self):
        self.client.login(username="author", password="pass123")
        response = self.client.post(self.url)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertRedirects(response, self.recipe_url)
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("Your comment has been deleted.", messages)

    def test_non_author_cannot_delete_comment(self):
        self.client.login(username="otheruser", password="pass123")
        response = self.client.post(self.url)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertRedirects(response, self.recipe_url)
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("You do not have permission to delete this comment.", messages)

    def test_unauthenticated_user_redirects_to_login(self):
        response = self.client.get(self.url)
        login_url = reverse("log_in")
        self.assertRedirects(response, f"{login_url}?next={self.url}")
