"""Tests for AdminLoginView."""

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from recipes.models import User


class AdminLoginViewTests(TestCase):
    def setUp(self):
        self.url = reverse("admin_login")
        self.admin_user = User.objects.create_user(
            username="@admin",
            password="Password123",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.staff_user = User.objects.create_user(
            username="@staff",
            password="Password123",
            email="staff@example.com",
            is_staff=True,
            is_superuser=False,
        )
        self.regular_user = User.objects.create_user(
            username="@regular",
            password="Password123",
            email="regular@example.com",
            is_staff=False,
            is_superuser=False,
        )

    def test_get_request_renders_admin_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["is_admin_login"])
        self.assertIn("admin_login.html", [t.name for t in response.templates])

    def test_admin_user_can_log_in(self):
        response = self.client.post(
            self.url, {"username": "@admin", "password": "Password123"}, follow=True
        )

        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin_user.id)
        self.assertTrue(response.redirect_chain)
        self.assertTrue(response.redirect_chain[-1][0].startswith("/admin/"))
        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        self.assertTrue(any("Welcome" in msg for msg in messages))

    def test_staff_user_can_log_in(self):
        response = self.client.post(
            self.url, {"username": "@staff", "password": "Password123"}, follow=True
        )

        self.assertEqual(int(self.client.session["_auth_user_id"]), self.staff_user.id)
        self.assertTrue(response.redirect_chain)
        self.assertTrue(response.redirect_chain[-1][0].startswith("/admin/"))

    def test_regular_user_gets_access_denied(self):
        response = self.client.post(
            self.url, {"username": "@regular", "password": "Password123"}, follow=True
        )

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)
        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        self.assertTrue(any("Access denied" in msg for msg in messages))

    def test_invalid_credentials_show_error(self):
        response = self.client.post(
            self.url,
            {"username": "doesnotexist", "password": "WrongPassword"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        self.assertTrue(any("Invalid" in msg for msg in messages))

    def test_already_logged_in_redirects(self):
        self.client.login(username="@admin", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
