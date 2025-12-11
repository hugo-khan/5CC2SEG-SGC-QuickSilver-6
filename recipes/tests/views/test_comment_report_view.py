from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from recipes.models import Comment, CommentReport

User = get_user_model()

class ReportCommentViewTest(TestCase):
    fixtures = ['other_users.json', 'sample_comment_data.json']

    def setUp(self):
        self.reporter = User.objects.get(username='@janedoe')
        self.comment_author = User.objects.get(username='@petrapickles')
        self.comment = Comment.objects.get(pk=1)
        self.url = reverse('report_comment')

        # Set a known password for fixture users for login
        self.reporter.set_password('pass')
        self.reporter.save()
        self.comment_author.set_password('pass')
        self.comment_author.save()

    def test_login_required(self):
        response = self.client.post(self.url, {'comment_id': self.comment.id, 'reason': 'Spam'})
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_create_report(self):
        self.client.login(username='@janedoe', password='pass')
        response = self.client.post(self.url, {'comment_id': self.comment.id, 'reason': 'Offensive'})
        self.assertEqual(CommentReport.objects.count(), 1)
        report = CommentReport.objects.first()
        self.assertEqual(report.comment, self.comment)
        self.assertEqual(report.reporter, self.reporter)

    def test_prevent_self_report(self):
        self.client.login(username='@petrapickles', password='pass')
        response = self.client.post(self.url, {'comment_id': self.comment.id, 'reason': 'Spam'})
        self.assertEqual(CommentReport.objects.count(), 0)

    def test_prevent_duplicate_report(self):
        self.client.login(username='@janedoe', password='pass')
        self.client.post(self.url, {'comment_id': self.comment.id, 'reason': 'Spam'})
        self.client.post(self.url, {'comment_id': self.comment.id, 'reason': 'Spam again'})
        self.assertEqual(CommentReport.objects.count(), 1)


