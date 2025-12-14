from django.test import TestCase
from django.urls import reverse

from recipes.forms.comment_form import CommentForm
from recipes.models import Comment, Recipe, User


class CommentViewTests(TestCase):
    def _create_recipe(self, author_username="alice"):
        author = User.objects.create_user(username=author_username, password="pass123")
        recipe = Recipe.objects.create(
            author=author,
            title="Test Recipe",
            name="Test Recipe",
            description="Test description",
            ingredients="a,b",
            instructions="mix",
            is_published=True,
        )
        return author, recipe

    def test_logged_in_user_can_post_comment(self):
        user, recipe = self._create_recipe()
        self.client.login(username=user.username, password="pass123")

        url = reverse("add_comment", args=[recipe.id])
        response = self.client.post(url, {"text": "Great recipe!"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)
        c = Comment.objects.first()
        self.assertEqual(c.text, "Great recipe!")
        self.assertEqual(c.recipe, recipe)
        self.assertEqual(c.user, user)

    def test_anonymous_user_cannot_post_comment(self):
        user, recipe = self._create_recipe("bob")

        url = reverse("add_comment", args=[recipe.id])
        response = self.client.post(url, {"text": "Nice!"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("/log_in", response.url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_form_rejects_empty_text(self):
        form = CommentForm(data={"text": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)

    def test_comment_form_accepts_valid_text(self):
        form = CommentForm(data={"text": "Tasty!"})
        self.assertTrue(form.is_valid())

    def test_recipe_page_displays_all_comments(self):
        user, recipe = self._create_recipe("carol")
        for t in ["one", "two", "three", "four"]:
            Comment.objects.create(recipe=recipe, user=user, text=t)

        response = self.client.get(reverse("recipe_detail", args=[recipe.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("comments", response.context)
        returned = response.context["comments"]

        self.assertEqual(len(returned), 4)
        self.assertEqual(returned[0].text, "four")
        self.assertEqual(returned[-1].text, "one")

    def test_feed_shows_only_top_three_comments(self):
        user, recipe = self._create_recipe("dave")
        for i in range(5):
            Comment.objects.create(recipe=recipe, user=user, text=f"Comment {i}")

        response = self.client.get(reverse("feed"))
        self.assertEqual(response.status_code, 200)

        comments_by_recipe = response.context["comments"]
        comments = comments_by_recipe[recipe.id]

        self.assertEqual(len(comments), 3)
        self.assertEqual(comments[0].text, "Comment 4")
        self.assertEqual(comments[1].text, "Comment 3")
        self.assertEqual(comments[2].text, "Comment 2")

    def test_comment_modal_exists_in_recipe_page(self):
        _, recipe = self._create_recipe("emily")

        response = self.client.get(reverse("recipe_detail", args=[recipe.id]))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        self.assertIn('id="commentModal"', html)
        self.assertIn('class="modal fade"', html)
        self.assertIn("<form", html)
        self.assertIn("add_comment", html)
        self.assertIn('<textarea', html)
        self.assertIn('name="text"', html)

    def test_comment_ordering_newest_first(self):
        user, recipe = self._create_recipe("frank")

        Comment.objects.create(recipe=recipe, user=user, text="Oldest")
        Comment.objects.create(recipe=recipe, user=user, text="Middle")
        Comment.objects.create(recipe=recipe, user=user, text="Newest")

        response = self.client.get(reverse("recipe_detail", args=[recipe.id]))
        comments = response.context["comments"]

        self.assertEqual(comments[0].text, "Newest")
        self.assertEqual(comments[1].text, "Middle")
        self.assertEqual(comments[2].text, "Oldest")
