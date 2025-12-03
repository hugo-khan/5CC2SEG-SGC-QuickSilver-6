# recipes/tests/models/test_signals.py

from django.test import TestCase
from django.contrib.auth import get_user_model

from recipes.models.recipe import Recipe
from recipes.models.follow import Follow
from recipes.models.like import Like
from recipes.models.saved_recipes import SavedRecipe
from recipes.models.comment import Comment


User = get_user_model()


class SignalTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="@user1", password="test1234")
        self.user2 = User.objects.create_user(username="@user2", password="test1234")
        self.recipe = Recipe.objects.create(
            user=self.user1,
            title="Test Recipe",
            description="desc",
            instructions="mix",
            cooking_time=10,
            servings=1,
        )

    # -----------------------------
    # FOLLOW SIGNALS
    # -----------------------------

    def test_follow_counts_update_on_follow(self):
        Follow.objects.create(follower=self.user1, followed=self.user2)

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

        self.assertEqual(self.user1.following_count, 1)
        self.assertEqual(self.user2.followers_count, 1)

    def test_follow_counts_update_on_unfollow(self):
        follow = Follow.objects.create(follower=self.user1, followed=self.user2)
        follow.delete()

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

        self.assertEqual(self.user1.following_count, 0)
        self.assertEqual(self.user2.followers_count, 0)

    # -----------------------------
    # LIKE SIGNALS
    # -----------------------------

    def test_like_count_increases(self):
        Like.objects.create(user=self.user1, recipe=self.recipe)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.likes_count, 1)

    def test_like_count_decreases(self):
        like = Like.objects.create(user=self.user1, recipe=self.recipe)
        like.delete()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.likes_count, 0)

    # -----------------------------
    # SAVED RECIPE SIGNALS
    # -----------------------------

    def test_save_count_increases(self):
        SavedRecipe.objects.create(user=self.user1, recipe=self.recipe)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.saves_count, 1)

    def test_save_count_decreases(self):
        sr = SavedRecipe.objects.create(user=self.user1, recipe=self.recipe)
        sr.delete()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.saves_count, 0)

    # -----------------------------
    # COMMENT SIGNALS
    # -----------------------------

    def test_comment_count_increases(self):
        Comment.objects.create(user=self.user1, recipe=self.recipe, text="Nice!")
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.comments_count, 1)

    def test_comment_count_decreases(self):
        c = Comment.objects.create(user=self.user1, recipe=self.recipe, text="Nice!")
        c.delete()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.comments_count, 0)
