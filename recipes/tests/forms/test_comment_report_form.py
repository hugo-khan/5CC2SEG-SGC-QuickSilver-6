from django.test import TestCase

from recipes.forms import CommentReportForm


class CommentReportFormTest(TestCase):

    def test_valid_form(self):
        form_data = {"reason": "This comment is offensive"}
        form = CommentReportForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["reason"], "This comment is offensive")

    def test_empty_reason_invalid(self):
        form_data = {"reason": ""}
        form = CommentReportForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("reason", form.errors)
