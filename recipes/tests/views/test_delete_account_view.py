"""Tests for the delete account view."""
from django.contrib import messages
from django.test import TestCase
from django.urls import reverse

from recipes.forms import DeleteAccountForm
from recipes.models import User
from recipes.tests.helpers import LogInTester, reverse_with_next


class DeleteAccountViewTestCase(TestCase, LogInTester):
    """Test suite for DeleteAccountView."""

    fixtures = ['recipes/tests/fixtures/default_user.json']

    def setUp(self):
        self.url = reverse('delete_account')
        self.user = User.objects.get(username='@johndoe')
        self.form_input = {
            'confirmation': 'DELETE',
            'password': 'Password123',
        }

    def test_delete_account_url(self):
        self.assertEqual(self.url, '/account/delete/')

    def test_get_delete_account(self):
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_account.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, DeleteAccountForm))

    def test_get_delete_account_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next('log_in', self.url)
        response = self.client.get(self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

    def test_successful_account_deletion(self):
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertRedirects(response, reverse('home'), status_code=302, target_status_code=200)
        self.assertFalse(User.objects.filter(username='@johndoe').exists())
        self.assertFalse(self._is_logged_in())
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_account_deletion_rejected_with_wrong_password(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['password'] = 'WrongPassword123'
        response = self.client.post(self.url, self.form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_account.html')
        self.assertTrue(User.objects.filter(username='@johndoe').exists())
        self.assertTrue(self._is_logged_in())

    def test_account_deletion_rejected_with_wrong_confirmation_phrase(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['confirmation'] = 'remove'
        response = self.client.post(self.url, self.form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_account.html')
        self.assertTrue(User.objects.filter(username='@johndoe').exists())
        self.assertTrue(self._is_logged_in())

    def test_post_delete_account_redirects_when_not_logged_in(self):
        response = self.client.post(self.url, self.form_input)
        redirect_url = reverse_with_next('log_in', self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTrue(User.objects.filter(username='@johndoe').exists())

    def test_delete_account_for_oauth_user(self):
        """Test that OAuth users can delete account without password."""
        # Create user without password (OAuth user)
        oauth_user = User.objects.create_user(
            username='@oauthuser',
            email='oauth@example.com',
            first_name='OAuth',
            last_name='User'
        )
        oauth_user.set_unusable_password()
        oauth_user.save()
        
        # Create social account
        try:
            from allauth.socialaccount.models import SocialAccount
            SocialAccount.objects.create(
                user=oauth_user,
                provider='google',
                uid='123456789',
                extra_data={}
            )
        except ImportError:
            pass
        
        self.client.login(username='@oauthuser', password='')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_oauth_user', response.context)
        self.assertTrue(response.context['is_oauth_user'])
        
        # Try to delete without password
        response = self.client.post(
            self.url,
            {'confirmation': 'DELETE'},
            follow=True
        )
        self.assertRedirects(response, reverse('home'), status_code=302, target_status_code=200)
        self.assertFalse(User.objects.filter(username='@oauthuser').exists())

    def test_delete_account_shows_oauth_info(self):
        """Test that delete account page shows OAuth info for OAuth users."""
        oauth_user = User.objects.create_user(
            username='@oauthuser',
            email='oauth@example.com'
        )
        oauth_user.set_unusable_password()
        oauth_user.save()
        
        try:
            from allauth.socialaccount.models import SocialAccount
            SocialAccount.objects.create(
                user=oauth_user,
                provider='google',
                uid='123456789',
                extra_data={}
            )
        except ImportError:
            pass
        
        self.client.login(username='@oauthuser', password='')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OAuth')

