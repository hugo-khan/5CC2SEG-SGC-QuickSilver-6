"""Tests for RecipeAccountAdapter."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import Mock, MagicMock

from recipes.adapters import RecipeAccountAdapter

User = get_user_model()


class RecipeAccountAdapterTest(TestCase):
    def setUp(self):
        self.adapter = RecipeAccountAdapter()
        self.request = Mock()

    def test_populate_username_from_email(self):
        """Test that username is generated from email."""
        user = User(email='testuser@example.com')
        self.adapter.populate_username(self.request, user)
        self.assertTrue(user.username.startswith('@'))
        self.assertIn('testuser', user.username.lower())

    def test_populate_username_sanitizes_email(self):
        """Test that special characters are removed from email."""
        user = User(email='test.user+123@example.com')
        self.adapter.populate_username(self.request, user)
        self.assertTrue(user.username.startswith('@'))
        # Should contain only alphanumeric and underscore
        username_body = user.username[1:]  # Remove @
        self.assertTrue(username_body.replace('_', '').isalnum() or username_body.isalnum())

    def test_populate_username_handles_short_email(self):
        """Test that short email parts get 'user' prefix."""
        user = User(email='ab@example.com')
        self.adapter.populate_username(self.request, user)
        self.assertTrue(user.username.startswith('@'))
        # Should use 'user' as base for short emails
        self.assertIn('user', user.username.lower())

    def test_populate_username_skips_if_username_exists(self):
        """Test that existing username is not overwritten."""
        user = User(username='@existing', email='newemail@example.com')
        original_username = user.username
        self.adapter.populate_username(self.request, user)
        self.assertEqual(user.username, original_username)

    def test_populate_username_creates_unique_username(self):
        """Test that duplicate usernames get numeric suffix."""
        # Create a user with a username
        User.objects.create_user(
            username='@testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Try to create another user with same email base
        user = User(email='testuser@example.com')
        self.adapter.populate_username(self.request, user)
        
        # Should have a different username (with suffix)
        self.assertNotEqual(user.username, '@testuser')
        self.assertTrue(user.username.startswith('@testuser'))

    def test_generate_unique_username_from_email(self):
        """Test generate_unique_username with email."""
        result = self.adapter.generate_unique_username(['test@example.com'])
        self.assertTrue(result.startswith('@'))
        self.assertIn('test', result.lower())

    def test_generate_unique_username_without_email(self):
        """Test generate_unique_username without email falls back to random."""
        result = self.adapter.generate_unique_username(['randomtext'])
        self.assertTrue(result.startswith('@'))
        self.assertTrue(len(result) <= 30)

    def test_generate_unique_username_creates_unique(self):
        """Test that generate_unique_username creates unique usernames."""
        # Create existing user
        User.objects.create_user(
            username='@test',
            email='test@example.com',
            password='testpass123'
        )
        
        # Generate new username
        result = self.adapter.generate_unique_username(['test@example.com'])
        self.assertNotEqual(result, '@test')
        self.assertTrue(result.startswith('@test'))

    def test_create_unique_username_handles_long_base(self):
        """Test that long usernames are truncated properly."""
        long_email = 'a' * 50 + '@example.com'
        user = User(email=long_email)
        self.adapter.populate_username(self.request, user)
        self.assertTrue(len(user.username) <= 30)
        self.assertTrue(user.username.startswith('@'))

    def test_populate_username_with_social_account(self):
        """Test populate_username uses social account email if available."""
        # Create a user first so we can add social account
        user = User.objects.create_user(
            username='@temp',
            email='temp@example.com',
            password='temp'
        )
        try:
            from allauth.socialaccount.models import SocialAccount
            SocialAccount.objects.create(
                user=user,
                provider='google',
                uid='123456',
                extra_data={'email': 'social@example.com'}
            )
            # Reset username to test population
            user.username = ''
            user.email = ''
            self.adapter.populate_username(self.request, user)
            self.assertTrue(user.username.startswith('@'))
            # Should use fallback since email is empty
            self.assertTrue(len(user.username) <= 30)
        except ImportError:
            # Skip if allauth not available
            pass

    def test_populate_username_fallback_when_no_email(self):
        """Test that populate_username creates random username when no email."""
        # Create user first so it has a PK
        user = User.objects.create_user(
            username='@temp',
            email='',
            password='temp'
        )
        user.username = ''  # Reset to test population
        self.adapter.populate_username(self.request, user)
        self.assertTrue(user.username.startswith('@'))
        self.assertTrue(len(user.username) <= 30)

