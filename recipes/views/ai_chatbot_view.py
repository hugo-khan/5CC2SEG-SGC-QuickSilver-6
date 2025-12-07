"""
Views for the AI Chef chatbot feature.

Provides:
- GET /ai/chef/ - Render chat UI
- POST /ai/chef/message/ - Process user message, run crew
- POST /ai/chef/publish/<draft_id>/ - Publish draft to Recipe
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from recipes.models import RecipeDraftSuggestion, ChatMessage
from recipes.ai.crew_service import run_suggestion, publish_from_draft, CrewServiceError
from recipes.ai.config import keys_configured

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
        user=user,
        status=RecipeDraftSuggestion.Status.DRAFT
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
        content=prompt + (f"\n\nDietary requirements: {dietary_requirements}" if dietary_requirements else ""),
    )
    
    try:
        # Run the crew workflow
        result = run_suggestion(prompt, dietary_requirements)
        
        # Create draft suggestion
        draft = RecipeDraftSuggestion.objects.create(
            user=user,
            prompt=prompt,
            dietary_requirements=dietary_requirements,
            draft_payload=result.get("form_fields", {}),
            assistant_display=result.get("assistant_display", ""),
            status=RecipeDraftSuggestion.Status.DRAFT,
        )
        
        # Store assistant message
        assistant_message = ChatMessage.objects.create(
            user=user,
            role=ChatMessage.Role.ASSISTANT,
            content=result.get("assistant_display", "I generated a recipe for you."),
            related_draft=draft,
        )
        
        if is_json_request:
            return JsonResponse({
                "success": True,
                "message": {
                    "role": "assistant",
                    "content": result.get("assistant_display", ""),
                },
                "draft": {
                    "id": draft.id,
                    "title": result.get("form_fields", {}).get("title", "Recipe"),
                    "publish_url": reverse("ai_chatbot_publish", kwargs={"draft_id": draft.id}),
                },
            })
        else:
            messages.success(request, "Recipe suggestion generated! Review it below.")
            return redirect("ai_chatbot")
        
    except CrewServiceError as e:
        logger.error(f"Crew service error: {e}")
        
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
            return JsonResponse({"error": "You can only publish your own drafts."}, status=403)
        else:
            messages.error(request, "You can only publish your own drafts.")
            return redirect("ai_chatbot")
    
    try:
        result = publish_from_draft(draft, user)
        
        # Add success message to chat
        ChatMessage.objects.create(
            user=user,
            role=ChatMessage.Role.ASSISTANT,
            content=f"🎉 Recipe published successfully! View it here: {result['recipe_url']}",
            related_draft=draft,
        )
        
        if is_json_request:
            return JsonResponse({
                "success": True,
                "recipe_id": result["recipe"].id,
                "recipe_url": result["recipe_url"],
                "message": "Recipe published successfully!",
            })
        else:
            messages.success(request, "Your recipe has been published!")
            return redirect("recipe_detail", pk=result["recipe"].id)
    
    except CrewServiceError as e:
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
        user=user,
        status=RecipeDraftSuggestion.Status.DRAFT
    ).delete()
    
    if is_json_request:
        return JsonResponse({"success": True, "message": "Chat history cleared."})
    else:
        messages.info(request, "Chat history cleared.")
        return redirect("ai_chatbot")

