from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.contrib.messages import get_messages


class AdminLoginViewTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="adminuser",
            password="adminpass",
            is_staff=True
        )

        self.normal_user = User.objects.create_user(
            username="normaluser",
            password="normalpass",
            is_staff=False
        )

        self.url = "/admin-login/"

    def test_get_request_renders_admin_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_login.html")
        self.assertIn("form", response.context)
        self.assertTrue(response.context["is_admin_login"])

    def test_admin_user_can_log_in(self):
        response = self.client.post(self.url, {
            "username": "adminuser",
            "password": "adminpass",
        })

        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin_user.id)
        self.assertRedirects(response, "/admin/")
        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        self.assertIn("Welcome, adminuser!", messages[0])

    def test_non_admin_user_gets_error(self):
        response = self.client.post(self.url, {
            "username": "normaluser",
            "password": "normalpass",
        })

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_login.html")
        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        self.assertIn("Access denied. This login is for administrators only.", messages[0])

    def test_invalid_credentials_show_error(self):
        response = self.client.post(self.url, {
            "username": "doesnotexist",
            "password": "wrongpass",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_login.html")
        messages = [str(msg) for msg in get_messages(response.wsgi_request)]
        self.assertIn("Invalid credentials", messages[0])

    def test_already_logged_in_redirects(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(self.url)
        self.assertRedirects(response, "/admin/")
