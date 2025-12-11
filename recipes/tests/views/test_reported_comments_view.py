from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from recipes.models import Comment, CommentReport, Recipe

User = get_user_model()


class ReportedCommentsViewTest(TestCase):
    fixtures = ["users.json", "recipes_and_comments.json"]

    def setUp(self):
        # Create admin user
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            is_staff=True
        )
        self.client.login(username="admin", password="adminpass")

        # Create a report for the existing comment
        self.comment = Comment.objects.first()
        self.report = CommentReport.objects.create(
            comment=self.comment,
            reporter=User.objects.get(pk=3),
            reason="Spam"
        )

    def admin_can_access_reported_comments_page(self):
        url = reverse("reported_comments")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.report.reason)

    def normal_user_cannot_access_reported_comments_page(self):
        self.client.logout()
        normal_user = User.objects.get(pk=2)
        self.client.login(username=normal_user.username, password="password")  # Assuming fixture password

        url = reverse("reported_comments")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirected

    def test_delete_comment_deletes_comment_and_reports(self):
        url = reverse("reported_comments")

        response = self.client.post(url, {
            "delete_comment": "1",
            "comment_id": self.comment.id,
        })

        self.assertRedirects(response, url)

        # Comment deleted
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

        # Report deleted too
        self.assertFalse(CommentReport.objects.filter(id=self.report.id).exists())

    def test_dismiss_report_only_deletes_report(self):
        url = reverse("reported_comments")

        response = self.client.post(url, {
            "dismiss_report": "1",
            "report_id": self.report.id,
        })

        self.assertRedirects(response, url)

        # Report deleted
        self.assertFalse(CommentReport.objects.filter(id=self.report.id).exists())

        # Comment still exists
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

