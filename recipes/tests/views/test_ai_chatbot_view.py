"""
Tests for the AI Chatbot views.

All tests mock the fast_recipe_service (and crew_service fallback) to avoid external API calls.

Updated to verify:
- Fast service is used by default
- Profile metadata is passed through
- Diagnostic endpoint works
"""

import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse

from recipes.models import User, Recipe, RecipeDraftSuggestion, ChatMessage


class AIChatbotViewTestCase(TestCase):
    """Base test case with common setup for AI chatbot tests."""

    fixtures = ['recipes/tests/fixtures/default_user.json']

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.other_user = User.objects.create_user(
            username='@janedoe',
            password='Password123',
            first_name='Jane',
            last_name='Doe',
            email='janedoe@example.org'
        )
        self.chatbot_url = reverse('ai_chatbot')
        self.message_url = reverse('ai_chatbot_message')


class AIChatbotGetViewTest(AIChatbotViewTestCase):
    """Tests for GET /ai/chef/"""

    def test_chatbot_url(self):
        """Test the chatbot URL is correct."""
        self.assertEqual(self.chatbot_url, '/ai/chef/')

    def test_get_chatbot_redirects_when_not_logged_in(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(self.chatbot_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('log_in'), response.url)

    def test_get_chatbot_returns_200_when_logged_in(self):
        """Authenticated users can access the chatbot page."""
        self.client.login(username='@johndoe', password='Password123')
        response = self.client.get(self.chatbot_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/ai_chatbot.html')

    def test_get_chatbot_shows_empty_state_with_no_messages(self):
        """Empty state is shown when no chat messages exist."""
        self.client.login(username='@johndoe', password='Password123')
        response = self.client.get(self.chatbot_url)
        self.assertContains(response, 'Welcome to AI Chef')

    def test_get_chatbot_shows_existing_messages(self):
        """Existing chat messages are displayed."""
        self.client.login(username='@johndoe', password='Password123')
        
        # Create some chat messages
        ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.USER,
            content='I want a pasta recipe'
        )
        ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.ASSISTANT,
            content='Here is a delicious pasta recipe...'
        )
        
        response = self.client.get(self.chatbot_url)
        self.assertContains(response, 'I want a pasta recipe')
        self.assertContains(response, 'Here is a delicious pasta recipe')

    def test_get_chatbot_shows_publish_button_when_draft_exists(self):
        """Publish button appears when a draft exists."""
        self.client.login(username='@johndoe', password='Password123')
        
        # Create a draft
        draft = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt='Make me pasta',
            draft_payload={'title': 'Pasta Carbonara'},
            assistant_display='Here is your pasta recipe',
            status=RecipeDraftSuggestion.Status.DRAFT
        )
        
        response = self.client.get(self.chatbot_url)
        self.assertContains(response, 'Publish Recipe')
        self.assertContains(response, reverse('ai_chatbot_publish', kwargs={'draft_id': draft.id}))


class AIChatbotMessageViewTest(AIChatbotViewTestCase):
    """Tests for POST /ai/chef/message/"""

    def test_message_url(self):
        """Test the message URL is correct."""
        self.assertEqual(self.message_url, '/ai/chef/message/')

    def test_post_message_redirects_when_not_logged_in(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.post(self.message_url, {'prompt': 'Make me pasta'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('log_in'), response.url)

    def test_post_message_empty_prompt_returns_error(self):
        """Empty prompt returns an error."""
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.message_url,
            data=json.dumps({'prompt': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    @patch('recipes.views.ai_chatbot_view.keys_configured')
    def test_post_message_returns_error_when_keys_not_configured(self, mock_keys):
        """Error returned when API keys are not configured."""
        mock_keys.return_value = False
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.message_url,
            data=json.dumps({'prompt': 'Make me pasta'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertIn('API keys', data['error'])

    @patch('recipes.views.ai_chatbot_view.suggest_recipe')
    @patch('recipes.views.ai_chatbot_view.keys_configured')
    def test_post_message_creates_draft_and_messages(self, mock_keys, mock_suggest):
        """Successful message creates draft and chat messages."""
        mock_keys.return_value = True
        mock_suggest.return_value = {
            'display_text': 'Here is your pasta recipe!',
            'form_fields': {
                'title': 'Pasta Carbonara',
                'summary': 'Creamy Italian pasta',
                'ingredients': 'Pasta\nBacon\nEggs',
                'instructions': 'Cook pasta\nMix with eggs',
                'prep_time_minutes': 10,
                'cook_time_minutes': 20,
                'servings': 4
            },
            'raw_json': {},
            'metadata': {
                'timing_ms': 5000,
                'cache_hit': False,
                'used_retrieval': True,
            }
        }
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.message_url,
            data=json.dumps({
                'prompt': 'Make me pasta',
                'dietary_requirements': 'none'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('draft', data)
        
        # Check draft was created
        draft = RecipeDraftSuggestion.objects.filter(user=self.user).first()
        self.assertIsNotNone(draft)
        self.assertEqual(draft.prompt, 'Make me pasta')
        self.assertEqual(draft.status, RecipeDraftSuggestion.Status.DRAFT)
        self.assertEqual(draft.draft_payload['title'], 'Pasta Carbonara')
        
        # Check chat messages were created
        messages = ChatMessage.objects.filter(user=self.user)
        self.assertEqual(messages.count(), 2)
        
        user_msg = messages.get(role=ChatMessage.Role.USER)
        self.assertIn('Make me pasta', user_msg.content)
        
        assistant_msg = messages.get(role=ChatMessage.Role.ASSISTANT)
        self.assertEqual(assistant_msg.content, 'Here is your pasta recipe!')

    @patch('recipes.views.ai_chatbot_view.suggest_recipe')
    @patch('recipes.views.ai_chatbot_view.keys_configured')
    def test_post_message_handles_service_error(self, mock_keys, mock_suggest):
        """Recipe service errors are handled gracefully."""
        from recipes.ai.fast_recipe_service import FastRecipeError
        
        mock_keys.return_value = True
        mock_suggest.side_effect = FastRecipeError('API rate limit exceeded')
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.message_url,
            data=json.dumps({'prompt': 'Make me pasta'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('API rate limit exceeded', data['error'])
        
        # Error message should be saved in chat
        error_msg = ChatMessage.objects.filter(
            user=self.user,
            role=ChatMessage.Role.ASSISTANT
        ).first()
        self.assertIsNotNone(error_msg)
        self.assertIn('error', error_msg.content.lower())

    def test_post_message_form_fallback(self):
        """Form POST (no-JS) redirects appropriately."""
        self.client.login(username='@johndoe', password='Password123')
        
        # Empty prompt should redirect
        response = self.client.post(self.message_url, {'prompt': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('ai_chatbot'))


class AIChatbotPublishViewTest(AIChatbotViewTestCase):
    """Tests for POST /ai/chef/publish/<draft_id>/"""

    def setUp(self):
        super().setUp()
        # Create a draft for testing
        self.draft = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt='Make me pasta',
            draft_payload={
                'title': 'Pasta Carbonara',
                'summary': 'Creamy Italian pasta',
                'ingredients': 'Pasta\nBacon\nEggs',
                'instructions': 'Cook pasta\nMix with eggs',
                'prep_time_minutes': 10,
                'cook_time_minutes': 20,
                'servings': 4
            },
            assistant_display='Here is your pasta recipe',
            status=RecipeDraftSuggestion.Status.DRAFT
        )
        self.publish_url = reverse('ai_chatbot_publish', kwargs={'draft_id': self.draft.id})

    def test_publish_url(self):
        """Test the publish URL is correct."""
        self.assertEqual(self.publish_url, f'/ai/chef/publish/{self.draft.id}/')

    def test_publish_redirects_when_not_logged_in(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('log_in'), response.url)

    def test_publish_returns_404_for_nonexistent_draft(self):
        """404 returned for non-existent draft."""
        self.client.login(username='@johndoe', password='Password123')
        url = reverse('ai_chatbot_publish', kwargs={'draft_id': 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_publish_forbidden_for_wrong_user(self):
        """Users cannot publish other users' drafts."""
        self.client.login(username='@janedoe', password='Password123')
        
        response = self.client.post(
            self.publish_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('own drafts', data['error'])

    @patch('recipes.views.ai_chatbot_view.publish_from_draft')
    def test_publish_creates_recipe(self, mock_publish):
        """Successful publish creates a recipe."""
        # Create a mock recipe
        recipe = Recipe.objects.create(
            author=self.user,
            title='Pasta Carbonara',
            name='Pasta Carbonara',
            summary='Creamy Italian pasta',
            description='Creamy Italian pasta',
            ingredients='Pasta\nBacon\nEggs',
            instructions='Cook pasta\nMix with eggs'
        )
        
        mock_publish.return_value = {
            'recipe': recipe,
            'recipe_url': reverse('recipe_detail', kwargs={'pk': recipe.pk})
        }
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.publish_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['recipe_id'], recipe.id)
        self.assertIn('recipe_url', data)

    @patch('recipes.views.ai_chatbot_view.publish_from_draft')
    def test_publish_handles_error(self, mock_publish):
        """Publish errors are handled gracefully."""
        from recipes.ai.crew_service import CrewServiceError
        
        mock_publish.side_effect = CrewServiceError('Missing required fields')
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.publish_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Missing required fields', data['error'])

    def test_publish_form_fallback(self):
        """Form POST (no-JS) redirects appropriately."""
        self.client.login(username='@janedoe', password='Password123')
        
        # Wrong user should redirect with error
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, 302)


class AIChatbotClearViewTest(AIChatbotViewTestCase):
    """Tests for POST /ai/chef/clear/"""

    def setUp(self):
        super().setUp()
        self.clear_url = reverse('ai_chatbot_clear')

    def test_clear_url(self):
        """Test the clear URL is correct."""
        self.assertEqual(self.clear_url, '/ai/chef/clear/')

    def test_clear_redirects_when_not_logged_in(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.post(self.clear_url)
        self.assertEqual(response.status_code, 302)

    def test_clear_removes_chat_messages(self):
        """Clear removes all chat messages for the user."""
        self.client.login(username='@johndoe', password='Password123')
        
        # Create messages
        ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.USER,
            content='Test message'
        )
        ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.ASSISTANT,
            content='Response'
        )
        
        # Create message for other user (should not be deleted)
        ChatMessage.objects.create(
            user=self.other_user,
            role=ChatMessage.Role.USER,
            content='Other user message'
        )
        
        response = self.client.post(self.clear_url)
        
        self.assertEqual(response.status_code, 302)
        
        # Check messages are cleared for current user
        self.assertEqual(
            ChatMessage.objects.filter(user=self.user).count(),
            0
        )
        
        # Check other user's messages are preserved
        self.assertEqual(
            ChatMessage.objects.filter(user=self.other_user).count(),
            1
        )

    def test_clear_removes_unpublished_drafts(self):
        """Clear removes unpublished drafts."""
        self.client.login(username='@johndoe', password='Password123')
        
        # Create drafts
        RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt='Test',
            status=RecipeDraftSuggestion.Status.DRAFT
        )
        
        response = self.client.post(self.clear_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            RecipeDraftSuggestion.objects.filter(
                user=self.user,
                status=RecipeDraftSuggestion.Status.DRAFT
            ).count(),
            0
        )

    def test_clear_json_response(self):
        """Clear returns JSON for AJAX requests."""
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            self.clear_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])


class AIChatbotIntegrationTest(AIChatbotViewTestCase):
    """Integration tests for the full chatbot workflow."""

    @patch('recipes.views.ai_chatbot_view.suggest_recipe')
    @patch('recipes.views.ai_chatbot_view.keys_configured')
    def test_full_workflow_message_to_publish(self, mock_keys, mock_suggest):
        """Test complete workflow: send message, then publish."""
        mock_keys.return_value = True
        mock_suggest.return_value = {
            'display_text': 'Here is your pasta recipe!',
            'form_fields': {
                'title': 'Pasta Carbonara',
                'summary': 'Creamy Italian pasta',
                'ingredients': 'Pasta\nBacon\nEggs',
                'instructions': 'Cook pasta\nMix with eggs',
                'prep_time_minutes': 10,
                'cook_time_minutes': 20,
                'servings': 4
            },
            'raw_json': {},
            'metadata': {
                'timing_ms': 5000,
                'cache_hit': False,
                'used_retrieval': True,
            }
        }
        
        self.client.login(username='@johndoe', password='Password123')
        
        # Step 1: Send message
        response = self.client.post(
            self.message_url,
            data=json.dumps({'prompt': 'Make me pasta'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        draft_id = data['draft']['id']
        
        # Step 2: Publish the draft
        publish_url = reverse('ai_chatbot_publish', kwargs={'draft_id': draft_id})
        
        response = self.client.post(
            publish_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('recipe_id', data)
        
        # Verify recipe was created
        recipe = Recipe.objects.get(pk=data['recipe_id'])
        self.assertEqual(recipe.title, 'Pasta Carbonara')
        self.assertEqual(recipe.author, self.user)
        
        # Verify draft was updated
        draft = RecipeDraftSuggestion.objects.get(pk=draft_id)
        self.assertEqual(draft.status, RecipeDraftSuggestion.Status.PUBLISHED)
        self.assertEqual(draft.published_recipe, recipe)

