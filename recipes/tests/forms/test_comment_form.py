from django.test import TestCase

from recipes.forms.comment_form import CommentForm


class CommentFormTests(TestCase):

    def test_valid_form(self):
        form = CommentForm(data={"text": "This is a test comment"})
        self.assertTrue(form.is_valid())

    def test_invalid_empty_comment(self):
        form = CommentForm(data={"text": ""})
        self.assertFalse(form.is_valid())
