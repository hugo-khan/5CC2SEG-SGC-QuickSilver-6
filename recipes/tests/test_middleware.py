"""Tests for AdminAccessMiddleware."""

from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from recipes.middleware import AdminAccessMiddleware

User = get_user_model()


class AdminAccessMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AdminAccessMiddleware(lambda request: None)

        self.admin_user = User.objects.create_user(
            username="@admin",
            password="Password123",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.regular_user = User.objects.create_user(
            username="@regular",
            password="Password123",
            email="regular@example.com",
            is_staff=False,
            is_superuser=False,
        )

    def _get_request(self, path, user=None):
        """Helper to create a request with user and messages."""
        request = self.factory.get(path)
        if user:
            request.user = user
        else:
            # Create an AnonymousUser for unauthenticated requests
            from django.contrib.auth.models import AnonymousUser

            request.user = AnonymousUser()

        # Add session and messages support
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        messages_middleware = MessageMiddleware(lambda req: None)
        messages_middleware.process_request(request)

        return request

    def test_allows_admin_login_page(self):
        """Test that admin login page is accessible."""
        request = self._get_request("/admin/login/")
        response = self.middleware(request)
        # Should not redirect (returns None from get_response)
        self.assertIsNone(response)

    def test_allows_admin_logout_page(self):
        """Test that admin logout page is accessible."""
        request = self._get_request("/admin/logout/")
        response = self.middleware(request)
        self.assertIsNone(response)

    def test_blocks_unauthenticated_user_from_admin(self):
        """Test that unauthenticated users are redirected from admin."""
        request = self._get_request("/admin/")
        response = self.middleware(request)
        # Should redirect to admin_login
        self.assertEqual(response.status_code, 302)
        # May redirect to /admin/login/ or our custom admin_login
        self.assertTrue("/admin/login" in response.url or "admin_login" in response.url)

    def test_blocks_regular_user_from_admin(self):
        """Test that regular users are redirected from admin."""
        request = self._get_request("/admin/", user=self.regular_user)
        response = self.middleware(request)
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        # May redirect to home or /
        self.assertTrue(
            response.url == "/" or "home" in response.url or response.url.endswith("/")
        )

    def test_allows_staff_user_to_admin(self):
        """Test that staff users can access admin."""
        request = self._get_request("/admin/", user=self.admin_user)
        response = self.middleware(request)
        # Should not redirect
        self.assertIsNone(response)

    def test_allows_superuser_to_admin(self):
        """Test that superusers can access admin."""
        superuser = User.objects.create_user(
            username="@super",
            password="Password123",
            email="super@example.com",
            is_staff=False,
            is_superuser=True,
        )
        request = self._get_request("/admin/", user=superuser)
        response = self.middleware(request)
        # Should not redirect
        self.assertIsNone(response)

    def test_non_admin_paths_are_not_blocked(self):
        """Test that non-admin paths are not affected."""
        request = self._get_request("/dashboard/")
        response = self.middleware(request)
        # Should not redirect
        self.assertIsNone(response)

    def test_admin_path_without_trailing_slash(self):
        """Test that admin paths without trailing slash are handled."""
        request = self._get_request("/admin/login")
        response = self.middleware(request)
        # Should not redirect (login page)
        self.assertIsNone(response)
