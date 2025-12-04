"""Tests for ProfileUpdateView."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from recipes.models import User


class ProfileUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='@user',
            password='Password123',
            first_name='Test',
            last_name='User',
            email='user@example.com'
        )

    def test_edit_profile_redirects_if_not_logged_in(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')))

    def test_edit_profile_loads_for_authenticated_user(self):
        """Test that edit profile page loads for authenticated users."""
        self.client.login(username='@user', password='Password123')
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')

    def test_edit_profile_shows_current_user_data(self):
        """Test that edit profile shows current user's data."""
        self.client.login(username='@user', password='Password123')
        response = self.client.get(reverse('profile_edit'))
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)
        self.assertContains(response, self.user.email)

    def test_edit_profile_updates_user_data(self):
        """Test that user can update their profile."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(
            reverse('profile_edit'),
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'updated@example.com',
                'bio': 'New bio',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_edit_profile_shows_success_message(self):
        """Test that success message is shown after update."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(
            reverse('profile_edit'),
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'updated@example.com',
            },
            follow=True
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('updated' in str(m).lower() for m in messages))

    def test_edit_profile_redirects_to_dashboard(self):
        """Test that after update, user is redirected to dashboard."""
        self.client.login(username='@user', password='Password123')
        response = self.client.post(
            reverse('profile_edit'),
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'updated@example.com',
            }
        )
        self.assertRedirects(response, reverse('dashboard'))

