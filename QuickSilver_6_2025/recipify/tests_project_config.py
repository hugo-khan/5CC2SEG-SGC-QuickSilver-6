# tests_project_config.py

import os
import sys
import importlib
from unittest import TestCase, mock
from pathlib import Path
from django.test import TestCase as DjangoTestCase
from django.urls import reverse, resolve
from django.conf import settings


# ==============================================================================
# 1. Tests for asgi.py and wsgi.py
# (Covers environment variable setup and application initialization)
# ==============================================================================

class TestAppConfigCoverage(TestCase):
    """Tests for recipify/asgi.py and recipify/wsgi.py."""

    @mock.patch('django.core.asgi.get_asgi_application')
    def test_asgi_config_coverage(self, mock_get_asgi):
        """Ensures recipify/asgi.py sets the settings module and calls get_asgi_application."""
        
        # Mock os.environ to ensure setdefault is tested in isolation
        with mock.patch.dict('os.environ', clear=True):
            # The code executes upon import
            import recipify.asgi
            
            # 1. Check if DJANGO_SETTINGS_MODULE was set
            self.assertEqual(os.environ.get('DJANGO_SETTINGS_MODULE'), 'recipify.settings')
            
            # 2. Check if get_asgi_application was called
            mock_get_asgi.assert_called_once()
            
            # 3. Check if 'application' is defined
            self.assertIsNotNone(recipify.asgi.application)
            
            # Clean up module cache for isolated testing
            del sys.modules['recipify.asgi']

    @mock.patch('django.core.wsgi.get_wsgi_application')
    def test_wsgi_config_coverage(self, mock_get_wsgi):
        """Ensures recipify/wsgi.py sets the settings module and calls get_wsgi_application."""
        
        # Mock os.environ to ensure setdefault is tested in isolation
        with mock.patch.dict('os.environ', clear=True):
            # The code executes upon import
            import recipify.wsgi
            
            # 1. Check if DJANGO_SETTINGS_MODULE was set
            self.assertEqual(os.environ.get('DJANGO_SETTINGS_MODULE'), 'recipify.settings')
            
            # 2. Check if get_wsgi_application was called
            mock_get_wsgi.assert_called_once()
            
            # 3. Check if 'application' is defined
            self.assertIsNotNone(recipify.wsgi.application)
            
            # Clean up module cache for isolated testing
            del sys.modules['recipify.wsgi']


# ==============================================================================
# 2. Tests for settings.py
# (Covers dynamic logic like GOOGLE_OAUTH_ENABLED)
# ==============================================================================

# Note: Django's test runner loads settings early. We must use a full
# reload with mocked environment variables to test the GOOGLE_OAUTH_ENABLED logic.

class TestProjectSettings(TestCase):
    """Tests for recipify/settings.py, focusing on dynamic logic."""

    def test_google_oauth_enabled_logic(self):
        """Tests the logic for GOOGLE_OAUTH_ENABLED based on environment variables."""
        
        # Case 1: Both ID and Secret are provided (Expected: True)
        mock_env_full = {
            'GOOGLE_CLIENT_ID': 'test_id_full', 
            'GOOGLE_CLIENT_SECRET': 'test_secret_full'
        }
        with mock.patch.dict(os.environ, mock_env_full, clear=True):
            # Reload module to apply mocked environment variables
            import recipify.settings
            importlib.reload(recipify.settings)
            
            self.assertTrue(recipify.settings.GOOGLE_OAUTH_ENABLED)
            self.assertEqual(recipify.settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'], 'test_id_full')
            self.assertEqual(recipify.settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'], 'test_secret_full')
            del sys.modules['recipify.settings']

        # Case 2: One or neither is provided (Expected: False)
        mock_env_partial = {
            'GOOGLE_CLIENT_ID': 'test_id_partial', 
            'GOOGLE_CLIENT_SECRET': ''
        }
        with mock.patch.dict(os.environ, mock_env_partial, clear=True):
            import recipify.settings
            importlib.reload(recipify.settings)
            
            self.assertFalse(recipify.settings.GOOGLE_OAUTH_ENABLED)
            self.assertEqual(recipify.settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'], 'test_id_partial')
            self.assertEqual(recipify.settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'], '')
            del sys.modules['recipify.settings']
            
    def test_base_settings_integrity(self):
        """Verifies key static settings are set correctly."""
        
        # When run via Django's test runner, the project settings are loaded.
        self.assertTrue(settings.DEBUG)
        self.assertEqual(settings.ROOT_URLCONF, 'recipify.urls')
        self.assertEqual(settings.AUTH_USER_MODEL, 'recipes.User')
        self.assertEqual(settings.LOGIN_REDIRECT_URL, 'dashboard')
        self.assertEqual(settings.STATIC_URL, 'static/')
        self.assertIsInstance(settings.BASE_DIR, Path)
        self.assertIn(settings.BASE_DIR / "static", settings.STATICFILES_DIRS)
        

# ==============================================================================
# 3. Tests for urls.py
# (Covers all defined URL patterns and the static file configuration)
# ==============================================================================

# Mock the necessary views from the 'recipes' app to allow urls.py to import
class MockView:
    """Mock class for simple function views (like home, dashboard, log_out)."""
    def __call__(self, request): return None

class MockClassView:
    """Mock class for Class-Based Views (like LogInView, PasswordView)."""
    @staticmethod
    def as_view():
        return lambda request: None

mock_views = {
    'home': MockView(),
    'dashboard': MockView(),
    'log_out': MockView(),
    'LogInView': MockClassView,
    'PasswordView': MockClassView,
    'ProfileUpdateView': MockClassView,
    'SignUpView': MockClassView,
    'DeleteAccountView': MockClassView,
}

# Apply the mock to the 'recipes.views' module before the urls.py import
@mock.patch.dict('sys.modules', {'recipes.views': mock.Mock(**mock_views)})
class TestProjectURLs(DjangoTestCase):
    """Tests for recipify/urls.py, covering all defined paths."""
    
    # Test all application-specific named URLs
    def test_app_urls_are_resolvable(self):
        """Checks that all custom paths are correctly defined and resolvable by name."""
        urls_to_test = {
            '/': 'home',
            '/dashboard/': 'dashboard',
            '/log_in/': 'log_in',
            '/log_out/': 'log_out',
            '/password/': 'password',
            '/profile/': 'profile',
            '/sign_up/': 'sign_up',
            '/account/delete/': 'delete_account',
        }
        
        for url_path, name in urls_to_test.items():
            with self.subTest(url_path=url_path):
                # Check resolution by name
                self.assertEqual(reverse(name), url_path)
                
                # Check resolution by path
                resolved_url = resolve(url_path)
                self.assertEqual(resolved_url.url_name, name)
                
    # Test built-in URLs (admin and allauth)
    def test_built_in_urls_are_resolvable(self):
        """Checks that included URL configs (admin and allauth) are resolvable."""
        
        # Admin URL
        self.assertEqual(reverse('admin:index'), '/admin/')
        
        # Allauth base path
        self.assertEqual(resolve('/accounts/').route, 'accounts/')

    # Test the static files configuration line for coverage
    @mock.patch('recipify.urls.static')
    def test_static_files_url_added(self, mock_static_func):
        """Ensures the static() function is called with the correct settings."""
        
        # The line being tested is:
        # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        
        # The mock function will return a list with a dummy item.
        mock_static_func.return_value = [mock.Mock()] 
        
        # Reload urls.py to re-run the static configuration line and apply the mock
        import recipify.urls
        importlib.reload(recipify.urls)
        
        # Check if the static function was called with the correct arguments (from Django settings)
        mock_static_func.assert_called_once_with(
            settings.STATIC_URL, 
            document_root=settings.STATIC_ROOT
        )
        
        # Check if the return value of static() was actually appended to urlpatterns
        self.assertIn(mock_static_func.return_value[0], recipify.urls.urlpatterns)
        
        # Clean up module cache
        del sys.modules['recipify.urls']