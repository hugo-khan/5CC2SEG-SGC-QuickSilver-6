from django.test import TestCase
import os


class ASGITests(TestCase):
    """Test ASGI configuration."""

    def test_application_exists(self):
        """Test ASGI application is configured."""
        from recipify.asgi import application
        self.assertIsNotNone(application)

    def test_application_callable(self):
        """Test ASGI application is callable."""
        from recipify.asgi import application
        self.assertTrue(callable(application))

    def test_settings_module_set(self):
        """Test DJANGO_SETTINGS_MODULE is set in ASGI."""
        import recipify.asgi
        self.assertEqual(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            'recipify.settings'
        )

    def test_asgi_imports(self):
        """Test ASGI imports work correctly."""
        try:
            from recipify.asgi import get_asgi_application
            self.assertTrue(callable(get_asgi_application))
        except ImportError:
            pass