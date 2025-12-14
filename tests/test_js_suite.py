import pathlib
from django.test import SimpleTestCase
from django.conf import settings
import quickjs


class TestJavaScriptSuite(SimpleTestCase):
    """Covers JS helpers using an embedded QuickJS runtime (no Node needed)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        project_root = pathlib.Path(settings.BASE_DIR)
        js_path = project_root / "static" / "js" / "ai_chatbot.js"
        if not js_path.exists():
            raise FileNotFoundError(f"JS source not found: {js_path}")

        cls.ctx = quickjs.Context()
        # Provide CommonJS-like exports before loading the file.
        cls.ctx.eval("var module = { exports: {} }; var exports = module.exports;")
        cls.ctx.eval(js_path.read_text())

        cls.escape_html = cls.ctx.eval("module.exports.escapeHtml")
        cls.build_message_html = cls.ctx.eval("module.exports.buildMessageHTML")
        cls.parse_draft_response = cls.ctx.eval("module.exports.parseDraftResponse")
        cls.get_csrf_token = cls.ctx.eval("module.exports.getCsrfToken")
        cls.build_publish_section_html = cls.ctx.eval("module.exports.buildPublishSectionHTML")

    # --- escapeHtml ------------------------------------------------------
    def test_escape_html_escapes_special_chars(self):
        result = self.escape_html.call('Tom & Jerry < "hi"')
        self.assertEqual(result, "Tom &amp; Jerry &lt; &quot;hi&quot;")

    def test_escape_html_non_string_returns_empty(self):
        self.assertEqual(self.escape_html.call(None), "")
        self.assertEqual(self.escape_html.call(123), "")

    # --- buildMessageHTML ------------------------------------------------
    def test_build_message_html_user_classes(self):
        html = self.build_message_html.call("user", "Hello", False)
        self.assertIn("chat-message-user", html)
        self.assertIn("bg-primary", html)
        self.assertIn("text-white", html)

    def test_build_message_html_assistant_header(self):
        html = self.build_message_html.call("assistant", "Hi", False)
        self.assertIn("chat-message-assistant", html)
        self.assertIn("AI Chef", html)

    def test_build_message_html_escapes_content(self):
        html = self.build_message_html.call("user", '<script>alert("x")</script>', False)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert", html)

    # --- parseDraftResponse ---------------------------------------------
    def test_parse_draft_response_invalid(self):
        result = self.parse_draft_response.call(None)
        self.assertFalse(result["success"])

    def test_parse_draft_response_success(self):
        payload = {
            "message": {"role": "assistant", "content": "Here"},
            "draft": {"id": 1, "title": "Pasta", "publish_url": "/publish/1/"},
        }
        result = self.parse_draft_response.call(payload)
        self.assertTrue(result["success"])
        self.assertEqual(result["draft"]["id"], 1)

    # --- getCsrfToken ---------------------------------------------------
    def test_get_csrf_token_without_dom(self):
        # In QuickJS there is no document; function should return null -> None
        self.assertIsNone(self.get_csrf_token.call())

    # --- buildPublishSectionHTML ----------------------------------------
    def test_build_publish_section_empty_when_missing_fields(self):
        self.assertEqual(self.build_publish_section_html.call(None, "t"), "")
        self.assertEqual(self.build_publish_section_html.call({"id": 1}, "t"), "")

    def test_build_publish_section_renders(self):
        draft = {"id": 2, "title": "Taco", "publish_url": "/publish/2/"}
        html = self.build_publish_section_html.call(draft, "csrf123")
        self.assertIn("publish-section", html)
        self.assertIn("Taco", html)
        self.assertIn("/publish/2/", html)
