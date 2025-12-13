from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from recipes.models import Comment, CommentReport, Recipe, User


class ReportCommentViewTest(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(
            username='@janedoe',
            password='pass',
            email='jane@example.com'
        )
        self.comment_author = User.objects.create_user(
            username='@petrapickles',
            password='pass',
            email='petra@example.com'
        )
        self.recipe = Recipe.objects.create(
            author=self.comment_author,
            title='Test Recipe',
            name='Test Recipe',
            description='Test description',
            ingredients='Test ingredients',
            instructions='Test instructions',
            is_published=True
        )
        self.comment = Comment.objects.create(
            recipe=self.recipe,
            user=self.comment_author,
            text='This is a test comment'
        )
        self.url = reverse('report_comments')

    def test_login_required(self):
        """Test that login is required to report a comment."""
        response = self.client.post(self.url, {'comment_id': self.comment.id, 'reason': 'Spam'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/log_in', response.url)

    def test_create_report(self):
        """Test that a user can create a report."""
        self.client.login(username='@janedoe', password='pass')
        response = self.client.post(
            self.url,
            {'comment_id': self.comment.id, 'reason': 'Offensive'},
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(CommentReport.objects.count(), 1)
        report = CommentReport.objects.first()
        self.assertEqual(report.comment, self.comment)
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.reason, 'Offensive')
        
        # Check success message
        messages_list = list(get_messages(response.wsgi_request))
        has_success_message = any('submitted' in str(m).lower() or 'thank' in str(m).lower() for m in messages_list)
        self.assertTrue(has_success_message)

    def test_prevent_self_report(self):
        """Test that users cannot report their own comments."""
        self.client.login(username='@petrapickles', password='pass')
        response = self.client.post(
            self.url,
            {'comment_id': self.comment.id, 'reason': 'Spam'},
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(CommentReport.objects.count(), 0)
        
        # Check error message
        messages_list = list(get_messages(response.wsgi_request))
        has_error_message = any('own comment' in str(m).lower() or 'cannot report' in str(m).lower() for m in messages_list)
        self.assertTrue(has_error_message)

    def test_prevent_duplicate_report(self):
        """Test that users cannot report the same comment twice."""
        self.client.login(username='@janedoe', password='pass')
        referer = reverse('recipe_detail', kwargs={'pk': self.recipe.pk})
        
        # First report
        self.client.post(
            self.url,
            {'comment_id': self.comment.id, 'reason': 'Spam'},
            HTTP_REFERER=referer
        )
        
        # Second report (should be prevented)
        response = self.client.post(
            self.url,
            {'comment_id': self.comment.id, 'reason': 'Spam again'},
            HTTP_REFERER=referer
        )
        
        self.assertEqual(CommentReport.objects.count(), 1)
        
        # Check info message
        messages_list = list(get_messages(response.wsgi_request))
        has_info_message = any('already reported' in str(m).lower() for m in messages_list)
        self.assertTrue(has_info_message)

    def test_invalid_form_shows_error(self):
        """Test that invalid form data shows error."""
        self.client.login(username='@janedoe', password='pass')
        response = self.client.post(
            self.url,
            {'comment_id': self.comment.id, 'reason': ''},  # Empty reason
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.pk})
        )
        
        # Should not create report
        self.assertEqual(CommentReport.objects.count(), 0)
        
        # Check error message
        messages_list = list(get_messages(response.wsgi_request))
        has_error_message = any('valid reason' in str(m).lower() or 'reason' in str(m).lower() for m in messages_list)
        self.assertTrue(has_error_message)

    def test_nonexistent_comment_returns_404(self):
        """Test that reporting nonexistent comment returns 404."""
        self.client.login(username='@janedoe', password='pass')
        response = self.client.post(
            self.url,
            {'comment_id': 99999, 'reason': 'Spam'},
            HTTP_REFERER=reverse('recipe_detail', kwargs={'pk': self.recipe.pk})
        )
        self.assertEqual(response.status_code, 404)


