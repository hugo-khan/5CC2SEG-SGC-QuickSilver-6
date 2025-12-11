from django.test import TestCase
from django.contrib.auth import get_user_model
from recipes.models import Comment, CommentReport

User = get_user_model()

class CommentReportModelTest(TestCase):
    fixtures = ['other_users.json', 'sample_comment_data.json']

    def setUp(self):
        self.user = User.objects.get(username='@janedoe')  # reporter
        self.comment = Comment.objects.get(pk=1)           # comment to report

    def test_create_report(self):
        report = CommentReport.objects.create(comment=self.comment, reporter=self.user, reason="Offensive")
        self.assertEqual(report.comment, self.comment)
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.reason, "Offensive")

    def test_prevent_duplicate_report(self):
        CommentReport.objects.create(comment=self.comment, reporter=self.user, reason="Spam")
        with self.assertRaises(Exception):
            CommentReport.objects.create(comment=self.comment, reporter=self.user, reason="Spam again")
