import os
import sys
from unittest import mock
from django.test import TestCase


class ManageCommandTests(TestCase):
    """Test manage.py command execution."""

    def test_main_function_executes(self):
        """Test that main() can be called without errors."""
        from manage import main
        
        with mock.patch('sys.argv', ['manage.py', 'check']):
            with mock.patch('django.core.management.execute_from_command_line') as mock_exec:
                main()
                mock_exec.assert_called_once()

    def test_django_settings_module_set(self):
        """Test that DJANGO_SETTINGS_MODULE is set correctly."""
        from manage import main
        
        os.environ.pop('DJANGO_SETTINGS_MODULE', None)
        
        with mock.patch('sys.argv', ['manage.py', 'check']):
            with mock.patch('django.core.management.execute_from_command_line'):
                main()
                self.assertEqual(
                    os.environ.get('DJANGO_SETTINGS_MODULE'),
                    'recipify.settings'
                )

    def test_import_error_handling(self):
        """Test that ImportError is raised when Django is not installed."""
        from manage import main
        
        with mock.patch('sys.argv', ['manage.py', 'check']):
            with mock.patch('django.core.management.execute_from_command_line',
                          side_effect=ImportError("Django not found")):
                with self.assertRaises(ImportError) as context:
                    main()
                self.assertIn("Couldn't import Django", str(context.exception))