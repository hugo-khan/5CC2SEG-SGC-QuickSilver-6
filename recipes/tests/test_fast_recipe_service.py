"""
Tests for the fast recipe service.

Tests cover:
1. Basic functionality (suggest_recipe returns correct structure)
2. Serper timeout fallback
3. Cache behavior (second call is faster / doesn't call external APIs)
4. Performance guard (max 1 LLM call per suggestion)
5. Publishing (pure Python, no LLM)
6. Profile counters are tracked correctly
7. Diagnostic endpoint works in DEBUG mode
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache

from recipes.models import User, Recipe


class FastRecipeServiceTestCase(TestCase):
    """Base test case for fast recipe service tests."""
    
    fixtures = ['recipes/tests/fixtures/default_user.json']
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        # Clear cache before each test
        cache.clear()
        
    def tearDown(self):
        cache.clear()


def _mock_successful_response():
    """Create a mock successful OpenAI response."""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "title": "Test Recipe",
                    "summary": "A test recipe",
                    "ingredients": ["Item 1", "Item 2"],
                    "instructions": ["Step 1", "Step 2"],
                    "prep_time_minutes": 10,
                    "cook_time_minutes": 20,
                    "servings": 4,
                    "dietary_notes": "",
                    "dietary_requirement": "vegetarian",
                    "difficulty": "medium",
                })
            }
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200}
    }


class SuggestRecipeBasicTest(FastRecipeServiceTestCase):
    """Tests for basic suggest_recipe functionality."""
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_suggest_recipe_returns_correct_structure(self, mock_keys, mock_post):
        """suggest_recipe returns dict with required keys."""
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        # Mock Serper response
        serper_response = MagicMock()
        serper_response.status_code = 200
        serper_response.json.return_value = {
            "organic": [
                {"title": "Test Recipe", "snippet": "A delicious test recipe"}
            ]
        }
        
        # Mock OpenAI response
        openai_response = MagicMock()
        openai_response.status_code = 200
        openai_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Pasta Carbonara",
                        "summary": "Creamy Italian pasta dish",
                        "ingredients": ["Pasta", "Bacon", "Eggs"],
                        "instructions": ["Cook pasta", "Fry bacon", "Mix with eggs"],
                        "prep_time_minutes": 10,
                        "cook_time_minutes": 20,
                        "servings": 4,
                        "dietary_notes": "Contains eggs and pork"
                    })
                }
            }]
        }
        
        # Configure mock to return different responses based on URL
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                return serper_response
            elif "openai" in url:
                return openai_response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        result = suggest_recipe("pasta carbonara", skip_cache=True)
        
        # Check structure
        self.assertIn("display_text", result)
        self.assertIn("form_fields", result)
        self.assertIn("raw_json", result)
        self.assertIn("metadata", result)
        
        # Check form_fields structure
        form_fields = result["form_fields"]
        self.assertIn("title", form_fields)
        self.assertIn("ingredients", form_fields)
        self.assertIn("instructions", form_fields)
        self.assertEqual(form_fields["title"], "Pasta Carbonara")
        
        # Check metadata
        metadata = result["metadata"]
        self.assertIn("timing_ms", metadata)
        self.assertIn("cache_hit", metadata)
        self.assertIn("used_retrieval", metadata)
        self.assertFalse(metadata["cache_hit"])
    
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_suggest_recipe_raises_error_when_keys_not_configured(self, mock_keys):
        """suggest_recipe raises FastRecipeError when API keys are missing."""
        from recipes.ai.fast_recipe_service import suggest_recipe, FastRecipeError
        
        mock_keys.return_value = False
        
        with self.assertRaises(FastRecipeError) as context:
            suggest_recipe("test")
        
        self.assertIn("API keys are not configured", str(context.exception))


class SerperTimeoutFallbackTest(FastRecipeServiceTestCase):
    """Tests for Serper timeout fallback behavior."""
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_serper_timeout_falls_back_to_llm_only(self, mock_keys, mock_post):
        """When Serper times out, recipe is still generated without search."""
        import requests
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        # Mock OpenAI response
        openai_response = MagicMock()
        openai_response.status_code = 200
        openai_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Simple Pasta",
                        "summary": "Quick and easy",
                        "ingredients": ["Pasta", "Sauce"],
                        "instructions": ["Boil pasta", "Add sauce"],
                        "prep_time_minutes": 5,
                        "cook_time_minutes": 10,
                        "servings": 2,
                        "dietary_notes": ""
                    })
                }
            }]
        }
        
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                raise requests.Timeout("Serper timeout")
            elif "openai" in url:
                return openai_response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        result = suggest_recipe("pasta", skip_cache=True)
        
        # Recipe should still be generated
        self.assertIn("display_text", result)
        self.assertEqual(result["form_fields"]["title"], "Simple Pasta")
        
        # Metadata should indicate no retrieval
        self.assertFalse(result["metadata"]["used_retrieval"])
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_serper_error_falls_back_gracefully(self, mock_keys, mock_post):
        """When Serper returns error, recipe generation continues."""
        import requests
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        # Mock responses
        serper_response = MagicMock()
        serper_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        
        openai_response = MagicMock()
        openai_response.status_code = 200
        openai_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Test Recipe",
                        "summary": "Test",
                        "ingredients": ["Ingredient"],
                        "instructions": ["Step 1"],
                        "prep_time_minutes": 5,
                        "cook_time_minutes": 5,
                        "servings": 1,
                        "dietary_notes": ""
                    })
                }
            }]
        }
        
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                return serper_response
            elif "openai" in url:
                return openai_response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        result = suggest_recipe("test", skip_cache=True)
        
        self.assertIn("display_text", result)
        self.assertFalse(result["metadata"]["used_retrieval"])


class CacheBehaviorTest(FastRecipeServiceTestCase):
    """Tests for caching behavior."""
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_cache_hit_does_not_call_external_apis(self, mock_keys, mock_post):
        """Second call with same params uses cache, not external APIs."""
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        # Setup mock responses
        serper_response = MagicMock()
        serper_response.status_code = 200
        serper_response.json.return_value = {"organic": []}
        
        openai_response = MagicMock()
        openai_response.status_code = 200
        openai_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Cached Recipe",
                        "summary": "From cache",
                        "ingredients": ["Item"],
                        "instructions": ["Step"],
                        "prep_time_minutes": 5,
                        "cook_time_minutes": 5,
                        "servings": 1,
                        "dietary_notes": ""
                    })
                }
            }]
        }
        
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                return serper_response
            elif "openai" in url:
                return openai_response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        # First call - should hit APIs
        result1 = suggest_recipe("test recipe")
        call_count_after_first = mock_post.call_count
        
        # Second call - should use cache
        result2 = suggest_recipe("test recipe")
        call_count_after_second = mock_post.call_count
        
        # Verify cache was used
        self.assertEqual(call_count_after_first, call_count_after_second)
        self.assertTrue(result2["metadata"]["cache_hit"])
        
        # Results should be identical
        self.assertEqual(result1["form_fields"], result2["form_fields"])
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_different_params_get_different_cache_entries(self, mock_keys, mock_post):
        """Different prompts create separate cache entries."""
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        call_count = [0]
        
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {"organic": []}
                return response
            elif "openai" in url:
                call_count[0] += 1
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "title": f"Recipe {call_count[0]}",
                                "summary": "Test",
                                "ingredients": ["Item"],
                                "instructions": ["Step"],
                                "prep_time_minutes": 5,
                                "cook_time_minutes": 5,
                                "servings": 1,
                                "dietary_notes": ""
                            })
                        }
                    }]
                }
                return response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        # Different prompts should result in different LLM calls
        result1 = suggest_recipe("chicken pasta")
        result2 = suggest_recipe("beef stew")
        
        self.assertEqual(result1["form_fields"]["title"], "Recipe 1")
        self.assertEqual(result2["form_fields"]["title"], "Recipe 2")


class PerformanceGuardTest(FastRecipeServiceTestCase):
    """Tests to guard against regression in number of LLM calls."""
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_only_one_llm_call_per_suggestion(self, mock_keys, mock_post):
        """Each suggest_recipe call makes at most 1 LLM call."""
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        llm_call_count = [0]
        
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {"organic": []}
                return response
            elif "openai" in url:
                llm_call_count[0] += 1
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = _mock_successful_response()
                return response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        # Make a request
        result = suggest_recipe("test", skip_cache=True)
        
        # Should be exactly 1 LLM call
        self.assertEqual(llm_call_count[0], 1, 
            f"Expected 1 LLM call, but got {llm_call_count[0]}")
        
        # Also verify via profile counters
        counters = result.get("metadata", {}).get("profile", {}).get("counters", {})
        self.assertEqual(counters.get("llm_calls", 0), 1,
            "Profile counters should show exactly 1 LLM call")
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    @patch('recipes.ai.fast_recipe_service.keys_configured')
    def test_profile_counters_track_operations(self, mock_keys, mock_post):
        """Profile counters correctly track all operations."""
        from recipes.ai.fast_recipe_service import suggest_recipe
        
        mock_keys.return_value = True
        
        def post_side_effect(url, **kwargs):
            if "serper" in url:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {
                    "organic": [{"title": "Test", "snippet": "A test recipe"}]
                }
                return response
            elif "openai" in url:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = _mock_successful_response()
                return response
            raise ValueError(f"Unexpected URL: {url}")
        
        mock_post.side_effect = post_side_effect
        
        result = suggest_recipe("test", skip_cache=True)
        
        counters = result.get("metadata", {}).get("profile", {}).get("counters", {})
        
        # Verify counters
        self.assertEqual(counters.get("llm_calls", 0), 1)
        self.assertEqual(counters.get("serper_calls", 0), 1)
        self.assertEqual(counters.get("cache_misses", 0), 2)  # serper cache + recipe cache
        self.assertEqual(counters.get("cache_hits", 0), 0)
        self.assertEqual(counters.get("errors", 0), 0)


class PublishingTest(FastRecipeServiceTestCase):
    """Tests for publishing functionality (pure Python, no LLM)."""
    
    def test_publish_recipe_from_fields_creates_recipe(self):
        """publish_recipe_from_fields creates a Recipe in the database."""
        from recipes.ai.fast_recipe_service import publish_recipe_from_fields
        
        form_fields = {
            "title": "Test Pasta",
            "summary": "A delicious test pasta",
            "ingredients": "Pasta\nSauce\nCheese",
            "instructions": "Cook pasta\nAdd sauce\nTop with cheese",
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "servings": 4,
            "dietary_requirement": "vegetarian",
            "difficulty": "medium",
        }
        
        recipe = publish_recipe_from_fields(form_fields, self.user)
        
        self.assertIsNotNone(recipe)
        self.assertIsNotNone(recipe.id)
        self.assertEqual(recipe.title, "Test Pasta")
        self.assertEqual(recipe.author, self.user)
        self.assertEqual(recipe.dietary_requirement, "vegetarian")
        self.assertEqual(recipe.difficulty, "medium")
        self.assertTrue(recipe.is_published)
    
    def test_publish_recipe_requires_title(self):
        """publish_recipe_from_fields raises error if title missing."""
        from recipes.ai.fast_recipe_service import publish_recipe_from_fields, FastRecipeError
        
        form_fields = {
            "ingredients": "Item",
            "instructions": "Step",
        }
        
        with self.assertRaises(FastRecipeError) as context:
            publish_recipe_from_fields(form_fields, self.user)
        
        self.assertIn("title", str(context.exception).lower())
    
    @patch('recipes.ai.fast_recipe_service.requests.post')
    def test_publish_does_not_call_llm(self, mock_post):
        """Publishing is pure Python and doesn't call any APIs."""
        from recipes.ai.fast_recipe_service import publish_recipe_from_fields
        
        form_fields = {
            "title": "No LLM Recipe",
            "summary": "Testing no LLM calls",
            "ingredients": "Item",
            "instructions": "Step",
        }
        
        publish_recipe_from_fields(form_fields, self.user)
        
        # No API calls should have been made
        mock_post.assert_not_called()


class FormatOutputTest(FastRecipeServiceTestCase):
    """Tests for output formatting (pure Python)."""
    
    def test_format_display_text_includes_all_sections(self):
        """_format_display_text includes title, ingredients, and instructions."""
        from recipes.ai.fast_recipe_service import _format_display_text
        
        recipe_json = {
            "title": "Test Recipe",
            "summary": "A test",
            "ingredients": ["1 cup flour", "2 eggs"],
            "instructions": ["Mix flour", "Add eggs"],
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "servings": 4,
            "dietary_notes": "Contains gluten"
        }
        
        display = _format_display_text(recipe_json)
        
        self.assertIn("Test Recipe", display)
        self.assertIn("1 cup flour", display)
        self.assertIn("Mix flour", display)
        self.assertIn("Contains gluten", display)
    
    def test_format_form_fields_matches_recipe_model(self):
        """_format_form_fields returns dict matching Recipe model fields."""
        from recipes.ai.fast_recipe_service import _format_form_fields
        
        recipe_json = {
            "title": "Model Test",
            "summary": "Testing fields",
            "ingredients": ["Item 1", "Item 2"],
            "instructions": ["Step 1", "Step 2"],
            "prep_time_minutes": 15,
            "cook_time_minutes": 30,
            "servings": 6,
            "dietary_requirement": "vegan",
            "difficulty": "hard",
        }
        
        fields = _format_form_fields(recipe_json)
        
        # Check all expected fields are present
        self.assertEqual(fields["title"], "Model Test")
        self.assertEqual(fields["summary"], "Testing fields")
        self.assertIn("Item 1", fields["ingredients"])
        self.assertIn("Step 1", fields["instructions"])
        self.assertEqual(fields["prep_time_minutes"], 15)
        self.assertEqual(fields["cook_time_minutes"], 30)
        self.assertEqual(fields["servings"], 6)
        self.assertEqual(fields["dietary_requirement"], "vegan")
        self.assertEqual(fields["difficulty"], "hard")


class ViewIntegrationTest(FastRecipeServiceTestCase):
    """Tests for view integration with fast service."""
    
    @patch('recipes.views.ai_chatbot_view.suggest_recipe')
    @patch('recipes.views.ai_chatbot_view.keys_configured')
    def test_view_uses_fast_service(self, mock_keys, mock_suggest):
        """AI chatbot view uses fast service when available."""
        from django.urls import reverse
        
        mock_keys.return_value = True
        mock_suggest.return_value = {
            "display_text": "Here is your recipe!",
            "form_fields": {
                "title": "Fast Recipe",
                "summary": "Quick and easy",
                "ingredients": "Items",
                "instructions": "Steps",
            },
            "raw_json": {},
            "metadata": {
                "timing_ms": 5000,
                "cache_hit": False,
                "used_retrieval": True,
                "profile": {"counters": {"llm_calls": 1}},
            },
        }
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            reverse('ai_chatbot_message'),
            data=json.dumps({"prompt": "quick pasta"}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["success"])
        self.assertEqual(data["draft"]["title"], "Fast Recipe")
        
        # Verify fast service was called
        mock_suggest.assert_called_once()


class DiagnosticEndpointTest(FastRecipeServiceTestCase):
    """Tests for the diagnostic endpoint."""
    
    def test_diagnostic_requires_login(self):
        """Diagnostic endpoint requires authentication."""
        from django.urls import reverse
        
        response = self.client.get(reverse('ai_diagnostic'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @override_settings(DEBUG=False)
    def test_diagnostic_disabled_in_production(self):
        """Diagnostic endpoint is disabled when DEBUG=False."""
        from django.urls import reverse
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.get(reverse('ai_diagnostic'))
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("DEBUG mode", data["error"])
    
    @override_settings(DEBUG=True)
    def test_diagnostic_get_returns_info(self):
        """GET request returns service information."""
        from django.urls import reverse
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.get(reverse('ai_diagnostic'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("service_type", data)
        self.assertIn("api_configured", data)
    
    @override_settings(DEBUG=True)
    @patch('recipes.views.ai_chatbot_view.suggest_recipe')
    @patch('recipes.views.ai_chatbot_view.keys_configured')
    def test_diagnostic_post_runs_test(self, mock_keys, mock_suggest):
        """POST request runs a diagnostic test."""
        from django.urls import reverse
        
        mock_keys.return_value = True
        mock_suggest.return_value = {
            "display_text": "Test recipe",
            "form_fields": {"title": "Diagnostic Test"},
            "raw_json": {},
            "metadata": {
                "timing_ms": 3000,
                "cache_hit": False,
                "used_retrieval": True,
                "profile": {
                    "stages": [
                        {"name": "llm_api_call", "duration_ms": 2500},
                        {"name": "serper_api_call", "duration_ms": 400},
                    ],
                    "total_ms": 3000,
                    "counters": {"llm_calls": 1, "serper_calls": 1},
                },
            },
        }
        
        self.client.login(username='@johndoe', password='Password123')
        
        response = self.client.post(
            reverse('ai_diagnostic'),
            data=json.dumps({"prompt": "test pasta"}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["success"])
        self.assertIn("timing_ms", data)
        self.assertIn("analysis", data)
        self.assertEqual(data["recipe_title"], "Diagnostic Test")

