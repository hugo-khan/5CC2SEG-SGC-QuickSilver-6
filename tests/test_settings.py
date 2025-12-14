from django.conf import settings
from django.test import TestCase


class SettingsTests(TestCase):
    """Test Django settings configuration."""

    def test_installed_apps_configuration(self):
        """Test that all required apps are installed."""
        required_apps = [
            "django.contrib.admin",
            "django.contrib.auth",
            "recipes",
        ]
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_database_configuration(self):
        """Test database configuration."""
        self.assertIn("default", settings.DATABASES)
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3"
        )

    def test_custom_user_model(self):
        """Test custom user model is configured."""
        self.assertEqual(settings.AUTH_USER_MODEL, "recipes.User")

    def test_allauth_configuration(self):
        """Test django-allauth settings."""
        self.assertEqual(settings.ACCOUNT_AUTHENTICATION_METHOD, "username_email")
        self.assertTrue(settings.ACCOUNT_EMAIL_REQUIRED)
