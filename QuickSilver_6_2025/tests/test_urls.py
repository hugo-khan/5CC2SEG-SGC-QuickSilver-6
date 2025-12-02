from django.test import TestCase
from django.urls import reverse


class URLConfigTests(TestCase):
    """Test URL configuration and routing."""

    def test_admin_url_resolves(self):
        """Test admin URL resolves correctly."""
        url = reverse('admin:index')
        self.assertEqual(url, '/admin/')

    def test_home_url_resolves(self):
        """Test home URL resolves to login view."""
        url = reverse('home')
        self.assertEqual(url, '/')

    def test_dashboard_url_resolves(self):
        """Test dashboard URL resolves."""
        url = reverse('dashboard')
        self.assertEqual(url, '/dashboard/')