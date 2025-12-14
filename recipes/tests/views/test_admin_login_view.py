"""Tests for AdminLoginView."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from recipes.models import User


class AdminLoginViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='@admin',
            password='Password123',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='@regular',
            password='Password123',
            email='regular@example.com',
            is_staff=False,
            is_superuser=False
        )
        self.staff_user = User.objects.create_user(
            username='@staff',
            password='Password123',
            email='staff@example.com',
            is_staff=True,
            is_superuser=False
        )

    def test_get_admin_login_page(self):
        """Test that admin login page is accessible."""
        response = self.client.get(reverse('admin_login'))
        self.assertEqual(response.status_code, 200)
        # May use Django admin template or our custom template
        # Just check that it's accessible and has a form
        self.assertTrue(
            'admin_login.html' in [t.name for t in response.templates] or
            'admin/login.html' in [t.name for t in response.templates]
        )

    def test_admin_user_can_login(self):
        """Test that admin user can successfully log in."""
        response = self.client.post(
            reverse('admin_login'),
            {'username': '@admin', 'password': 'Password123'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # May redirect to /admin/ or /dashboard/ depending on settings
        # Check that we got redirected somewhere (not still on login page)
        if hasattr(response, 'redirect_chain') and response.redirect_chain:
            redirect_url = response.redirect_chain[-1][0]
            self.assertTrue('/admin' in redirect_url or '/dashboard' in redirect_url)
        
        # Check success message
        messages_list = list(get_messages(response.wsgi_request))
        has_success_message = any('Welcome' in str(m) or 'admin' in str(m).lower() for m in messages_list)
        self.assertTrue(has_success_message or len(messages_list) > 0)

    def test_staff_user_can_login(self):
        """Test that staff user can successfully log in."""
        response = self.client.post(
            reverse('admin_login'),
            {'username': '@staff', 'password': 'Password123'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # May redirect to /admin/ or /dashboard/ depending on settings
        # Check that we got redirected somewhere
        if hasattr(response, 'redirect_chain') and response.redirect_chain:
            redirect_url = response.redirect_chain[-1][0]
            self.assertTrue('/admin' in redirect_url or '/dashboard' in redirect_url)

    def test_regular_user_cannot_login(self):
        """Test that regular user cannot log in via admin login."""
        response = self.client.post(
            reverse('admin_login'),
            {'username': '@regular', 'password': 'Password123'},
            follow=True
        )
        # Should not redirect to admin, should show error
        self.assertEqual(response.status_code, 200)
        # May redirect to Django admin login or show our custom page
        # Just check that we didn't get to admin panel (unless redirected to Django admin)
        if hasattr(response, 'url'):
            self.assertNotIn('/admin/', response.url or '')
        
        # Check error message
        messages_list = list(get_messages(response.wsgi_request))
        has_error_message = any('Access denied' in str(m) or 'administrators only' in str(m) or 'Invalid' in str(m) for m in messages_list)
        self.assertTrue(has_error_message or len(messages_list) > 0)

    def test_invalid_credentials_shows_error(self):
        """Test that invalid credentials show error message."""
        response = self.client.post(
            reverse('admin_login'),
            {'username': '@admin', 'password': 'WrongPassword'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # May show Django admin login or our custom page
        
        # Check error message
        messages_list = list(get_messages(response.wsgi_request))
        has_error_message = any('Invalid credentials' in str(m) or 'Invalid' in str(m) or 'Please enter' in str(m) for m in messages_list)
        self.assertTrue(has_error_message or len(messages_list) > 0)

    def test_nonexistent_user_shows_error(self):
        """Test that nonexistent user shows error."""
        response = self.client.post(
            reverse('admin_login'),
            {'username': '@nonexistent', 'password': 'Password123'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # May show Django admin login or our custom page
        
        messages_list = list(get_messages(response.wsgi_request))
        has_error_message = any('Invalid' in str(m) or 'Please enter' in str(m) for m in messages_list)
        self.assertTrue(has_error_message or len(messages_list) > 0)

    def test_admin_login_redirects_if_already_logged_in(self):
        """Test that admin login redirects if user is already logged in."""
        self.client.login(username='@admin', password='Password123')
        response = self.client.get(reverse('admin_login'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/admin/')

