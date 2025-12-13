import io
import sys
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command

# Import the script as a module
import importlib


class TestMakeAdminScript(TestCase):

    def setUp(self):
        from recipes.models import User
        self.User = User

    def run_script(self, argv):
        """Helper to run the script with fake command-line args."""
        with patch.object(sys, "argv", argv):
            output = io.StringIO()
            with patch("sys.stdout", output):
                importlib.invalidate_caches()
                import make_admin   # runs on import
        return output.getvalue()

    def test_make_user_admin(self):
        """Script should elevate an existing user to admin."""

        user = self.User.objects.create_user(
            username="@john",
            email="john@example.com",
            password="pass123"
        )

        output = self.run_script(["make_admin.py", "@john"])

        # Refresh from DB
        user.refresh_from_db()

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        self.assertIn("Successfully made @john an admin", output)

    def test_user_not_found(self):
        """Script should show error and similar users if username does not exist."""

        # Create user to match similar search
        similar = self.User.objects.create_user(
            username="@johndoe123",
            email="a@a.com",
            password="pass"
        )

        output = self.run_script(["make_admin.py", "@unknown"])

        self.assertIn("User '@unknown' not found", output)
        self.assertIn("Found similar users", output)
        self.assertIn(similar.username, output)
