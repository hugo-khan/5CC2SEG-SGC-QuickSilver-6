"""
Views for the AI Chef chatbot feature.

Provides:
- GET /ai/chef/ - Render chat UI
- POST /ai/chef/message/ - Process user message, generate recipe
- POST /ai/chef/publish/<draft_id>/ - Publish draft to Recipe
- GET /ai/chef/diagnostic/ - Performance diagnostic endpoint (DEBUG only)

Performance optimized: Uses fast_recipe_service for ~10s response times.
"""

import json
import logging
import time

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from recipes.ai.config import keys_configured
from recipes.models import ChatMessage, RecipeDraftSuggestion

# Use fast service by default (fallback to crew_service if needed)
try:
    from recipes.ai.fast_recipe_service import FastRecipeError, suggest_recipe

    USE_FAST_SERVICE = True
except ImportError:
    USE_FAST_SERVICE = False

# Import crew_service for fallback and publishing
try:
    from recipes.ai.crew_service import CrewServiceError, run_suggestion
except ImportError:
    run_suggestion = None
    CrewServiceError = Exception

# Publisher is always from crew_service (it's pure Python, no LLM)
from recipes.ai.crew_service import CrewServiceError as PublishError
from recipes.ai.crew_service import publish_from_draft

logger = logging.getLogger(__name__)


@login_required
def ai_chatbot(request):
    """
    Render the AI Chef chat interface.

    GET /ai/chef/

    Displays:
    - Chat transcript (user and assistant messages)
    - Latest draft if available
    - Input form for new messages
    """
    user = request.user

    # Get chat history for this user
    chat_messages = ChatMessage.objects.filter(user=user).order_by("created_at")

    # Get the latest draft (if any)
    latest_draft = RecipeDraftSuggestion.objects.filter(
        user=user, status=RecipeDraftSuggestion.Status.DRAFT
    ).first()

    # Check if API keys are configured
    api_configured = keys_configured()

    context = {
        "chat_messages": chat_messages,
        "latest_draft": latest_draft,
        "api_configured": api_configured,
    }

    return render(request, "recipes/ai_chatbot.html", context)


@login_required
@require_http_methods(["POST"])
def ai_chatbot_message(request):
    """
    Process a user message and generate a recipe suggestion.

    POST /ai/chef/message/

    Accepts:
    - prompt: User's recipe request (required)
    - dietary_requirements: Optional dietary restrictions

    Returns:
    - JSON response with assistant message and draft info (for JS clients)
    - Redirect with messages (for no-JS fallback)
    """
    user = request.user

    # Check for JSON or form data
    is_json_request = request.content_type == "application/json"

    if is_json_request:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        data = request.POST

    prompt = data.get("prompt", "").strip()
    dietary_requirements = data.get("dietary_requirements", "").strip()

    if not prompt:
        if is_json_request:
            return JsonResponse({"error": "Please enter a recipe request."}, status=400)
        else:
            messages.error(request, "Please enter a recipe request.")
            return redirect("ai_chatbot")

    # Check if API keys are configured
    if not keys_configured():
        error_msg = (
            "AI features are not available. API keys need to be configured. "
            "Please contact the administrator."
        )
        if is_json_request:
            return JsonResponse({"error": error_msg}, status=503)
        else:
            messages.error(request, error_msg)
            return redirect("ai_chatbot")

    # Store user message
    user_message = ChatMessage.objects.create(
        user=user,
        role=ChatMessage.Role.USER,
        content=prompt
        + (
            f"\n\nDietary requirements: {dietary_requirements}"
            if dietary_requirements
            else ""
        ),
    )

    try:
        # Use fast service or fallback to crew service
        if USE_FAST_SERVICE:
            result = suggest_recipe(prompt, dietary_requirements)
            display_text = result.get("display_text", "")
            form_fields = result.get("form_fields", {})
            metadata = result.get("metadata", {})

            # Log performance
            timing_ms = metadata.get("timing_ms", 0)
            cache_hit = metadata.get("cache_hit", False)
            logger.info(
                f"Recipe generated in {timing_ms:.0f}ms (cache_hit={cache_hit})"
            )
        else:
            # Fallback to old crew service
            result = run_suggestion(prompt, dietary_requirements)
            display_text = result.get("assistant_display", "")
            form_fields = result.get("form_fields", {})

        # Create draft suggestion
        draft = RecipeDraftSuggestion.objects.create(
            user=user,
            prompt=prompt,
            dietary_requirements=dietary_requirements,
            draft_payload=form_fields,
            assistant_display=display_text,
            status=RecipeDraftSuggestion.Status.DRAFT,
        )

        # Store assistant message
        assistant_message = ChatMessage.objects.create(
            user=user,
            role=ChatMessage.Role.ASSISTANT,
            content=display_text or "I generated a recipe for you.",
            related_draft=draft,
        )

        response_data = {
            "success": True,
            "message": {
                "role": "assistant",
                "content": display_text,
            },
            "draft": {
                "id": draft.id,
                "title": form_fields.get("title", "Recipe"),
                "publish_url": reverse(
                    "ai_chatbot_publish", kwargs={"draft_id": draft.id}
                ),
            },
        }

        # Include metadata for debugging (only in DEBUG mode)
        from django.conf import settings

        if getattr(settings, "DEBUG", False) and USE_FAST_SERVICE:
            response_data["_debug"] = {
                "timing_ms": metadata.get("timing_ms"),
                "cache_hit": metadata.get("cache_hit"),
                "used_retrieval": metadata.get("used_retrieval"),
            }

        if is_json_request:
            return JsonResponse(response_data)
        else:
            messages.success(request, "Recipe suggestion generated! Review it below.")
            return redirect("ai_chatbot")

    except FastRecipeError if USE_FAST_SERVICE else CrewServiceError as e:
        logger.error(f"Recipe service error: {e}")

        # Store error as assistant message
        ChatMessage.objects.create(
            user=user,
            role=ChatMessage.Role.ASSISTANT,
            content=f"I'm sorry, I couldn't generate a recipe. Error: {str(e)}",
        )

        if is_json_request:
            return JsonResponse({"error": str(e)}, status=500)
        else:
            messages.error(request, f"Failed to generate recipe: {str(e)}")
            return redirect("ai_chatbot")

    except Exception as e:
        logger.exception(f"Unexpected error in AI chatbot: {e}")

        # Store error as assistant message
        ChatMessage.objects.create(
            user=user,
            role=ChatMessage.Role.ASSISTANT,
            content="I'm sorry, an unexpected error occurred. Please try again.",
        )

        if is_json_request:
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)
        else:
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect("ai_chatbot")


@login_required
@require_http_methods(["POST"])
def ai_chatbot_publish(request, draft_id):
    """
    Publish a draft recipe to the database.

    POST /ai/chef/publish/<draft_id>/

    Only the owner of the draft can publish it.

    Returns:
    - JSON response with recipe URL (for JS clients)
    - Redirect to recipe detail (for no-JS fallback)
    """
    user = request.user
    is_json_request = request.content_type == "application/json"

    # Get the draft (404 if not found)
    draft = get_object_or_404(RecipeDraftSuggestion, id=draft_id)

    # Check ownership
    if draft.user != user:
        if is_json_request:
            return JsonResponse(
                {"error": "You can only publish your own drafts."}, status=403
            )
        else:
            messages.error(request, "You can only publish your own drafts.")
            return redirect("ai_chatbot")

    try:
        result = publish_from_draft(draft, user)

        # Add success message to chat with clickable link
        recipe_url = result["recipe_url"]
        ChatMessage.objects.create(
            user=user,
            role=ChatMessage.Role.ASSISTANT,
            content=f'🎉 Recipe published successfully! View it <a href="{recipe_url}" class="fw-bold">here</a>.',
            related_draft=draft,
        )

        if is_json_request:
            return JsonResponse(
                {
                    "success": True,
                    "recipe_id": result["recipe"].id,
                    "recipe_url": result["recipe_url"],
                    "message": "Recipe published successfully!",
                }
            )
        else:
            messages.success(request, "Your recipe has been published!")
            return redirect("recipe_detail", pk=result["recipe"].id)

    except PublishError as e:
        logger.error(f"Publish error: {e}")

        if is_json_request:
            return JsonResponse({"error": str(e)}, status=400)
        else:
            messages.error(request, str(e))
            return redirect("ai_chatbot")

    except Exception as e:
        logger.exception(f"Unexpected publish error: {e}")

        if is_json_request:
            return JsonResponse({"error": "Failed to publish recipe."}, status=500)
        else:
            messages.error(request, "Failed to publish recipe. Please try again.")
            return redirect("ai_chatbot")


@login_required
@require_http_methods(["POST"])
def ai_chatbot_clear(request):
    """
    Clear the chat history for the current user.

    POST /ai/chef/clear/
    """
    user = request.user
    is_json_request = request.content_type == "application/json"

    # Delete all chat messages for this user
    ChatMessage.objects.filter(user=user).delete()

    # Optionally clear unpublished drafts
    RecipeDraftSuggestion.objects.filter(
        user=user, status=RecipeDraftSuggestion.Status.DRAFT
    ).delete()

    if is_json_request:
        return JsonResponse({"success": True, "message": "Chat history cleared."})
    else:
        messages.info(request, "Chat history cleared.")
        return redirect("ai_chatbot")


@login_required
@require_http_methods(["GET", "POST"])
def ai_diagnostic(request):
    """
    Performance diagnostic endpoint for the AI service.

    GET /ai/chef/diagnostic/ - Show diagnostic form
    POST /ai/chef/diagnostic/ - Run diagnostic and return timing data

    Only available in DEBUG mode.
    """
    if not getattr(django_settings, "DEBUG", False):
        return JsonResponse(
            {"error": "Diagnostic endpoint only available in DEBUG mode"}, status=403
        )

    if request.method == "GET":
        # Return a simple diagnostic form
        return JsonResponse(
            {
                "message": "AI Diagnostic Endpoint",
                "usage": 'POST to this endpoint with JSON: {"prompt": "test prompt", "dietary": "optional"}',
                "service_type": (
                    "fast_recipe_service" if USE_FAST_SERVICE else "crew_service (slow)"
                ),
                "api_configured": keys_configured(),
            }
        )

    # POST - Run diagnostic
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    prompt = data.get("prompt", "simple pasta recipe")
    dietary = data.get("dietary", "")
    skip_cache = data.get(
        "skip_cache", True
    )  # Default to skip cache for accurate timing

    if not keys_configured():
        return JsonResponse(
            {
                "error": "API keys not configured",
                "service_type": (
                    "fast_recipe_service" if USE_FAST_SERVICE else "crew_service"
                ),
            },
            status=503,
        )

    start_time = time.perf_counter()

    try:
        if USE_FAST_SERVICE:
            result = suggest_recipe(prompt, dietary, skip_cache=skip_cache)
            total_time = (time.perf_counter() - start_time) * 1000

            return JsonResponse(
                {
                    "success": True,
                    "service": "fast_recipe_service",
                    "timing_ms": round(total_time, 1),
                    "profile": result.get("metadata", {}).get("profile", {}),
                    "cache_hit": result.get("metadata", {}).get("cache_hit", False),
                    "used_retrieval": result.get("metadata", {}).get(
                        "used_retrieval", False
                    ),
                    "recipe_title": result.get("form_fields", {}).get(
                        "title", "Unknown"
                    ),
                    "analysis": _analyze_timing(
                        result.get("metadata", {}).get("profile", {})
                    ),
                }
            )
        else:
            # Old crew service
            result = run_suggestion(prompt, dietary)
            total_time = (time.perf_counter() - start_time) * 1000

            return JsonResponse(
                {
                    "success": True,
                    "service": "crew_service",
                    "timing_ms": round(total_time, 1),
                    "warning": "Using slow crew_service. fast_recipe_service should be used instead.",
                }
            )

    except Exception as e:
        total_time = (time.perf_counter() - start_time) * 1000
        logger.exception(f"Diagnostic failed: {e}")
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
                "timing_ms": round(total_time, 1),
                "service": (
                    "fast_recipe_service" if USE_FAST_SERVICE else "crew_service"
                ),
            },
            status=500,
        )


def _analyze_timing(profile: dict) -> dict:
    """Analyze timing profile and provide recommendations."""
    stages = profile.get("stages", [])
    total_ms = profile.get("total_ms", 0)
    counters = profile.get("counters", {})

    analysis = {
        "total_ms": total_ms,
        "status": (
            "GOOD" if total_ms < 15000 else ("OK" if total_ms < 25000 else "SLOW")
        ),
        "recommendations": [],
    }

    # Check LLM calls
    llm_calls = counters.get("llm_calls", 0)
    if llm_calls > 1:
        analysis["recommendations"].append(
            f"WARNING: {llm_calls} LLM calls detected. Should be 1 maximum."
        )

    # Find slow stages
    for stage in stages:
        if stage["duration_ms"] > 10000:
            analysis["recommendations"].append(
                f"SLOW: {stage['name']} took {stage['duration_ms']:.0f}ms"
            )

    # Check serper
    serper_stage = next((s for s in stages if "serper" in s["name"]), None)
    if serper_stage and serper_stage["duration_ms"] > 4000:
        analysis["recommendations"].append(
            "Serper timeout may be too long or not working"
        )

    if not analysis["recommendations"]:
        analysis["recommendations"].append("All stages within expected limits")

    return analysis
