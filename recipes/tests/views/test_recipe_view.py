"""Tests for recipe_view helper functions."""

from django.test import TestCase

from recipes.forms import CommentForm
from recipes.views.recipe_view import add_comment_form_to_context


class RecipeViewHelperTest(TestCase):
    def test_add_comment_form_to_context(self):
        """Test that add_comment_form_to_context adds comment form to context."""
        context = {}
        mock_view = None  # Not actually used in the function

        result = add_comment_form_to_context(mock_view, context)

        self.assertIn("comment_form", result)
        self.assertIsInstance(result["comment_form"], CommentForm)
        self.assertIs(result, context)  # Should return the same context dict
