"""
Models for AI chatbot functionality.

RecipeDraftSuggestion: Stores AI-generated recipe drafts before publishing.
ChatMessage: Stores chat transcript between user and AI assistant.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class RecipeDraftSuggestion(models.Model):
    """
    Stores AI-generated recipe suggestions before they are published.
    
    A draft can be:
    - DRAFT: Generated but not yet published
    - PUBLISHED: Successfully published as a Recipe
    - FAILED: Generation or publishing failed
    """
    
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        FAILED = "FAILED", "Failed"
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipe_drafts",
    )
    prompt = models.TextField(
        help_text="The original user prompt that generated this recipe"
    )
    dietary_requirements = models.TextField(
        blank=True,
        default="",
        help_text="Optional dietary restrictions specified by the user"
    )
    draft_payload = models.JSONField(
        default=dict,
        help_text="Structured recipe data from AI (form_fields dict)"
    )
    assistant_display = models.TextField(
        blank=True,
        default="",
        help_text="Formatted display text for the chat interface"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_draft",
        help_text="Link to the published Recipe if status is PUBLISHED"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recipe Draft Suggestion"
        verbose_name_plural = "Recipe Draft Suggestions"
    
    def __str__(self):
        title = self.draft_payload.get("title", "Untitled")
        return f"Draft: {title} ({self.status})"


class ChatMessage(models.Model):
    """
    Stores individual chat messages in a conversation.
    
    Each message has a role:
    - user: Message from the user
    - assistant: Response from the AI
    """
    
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    thread_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Optional thread identifier for grouping conversations"
    )
    # Link to the draft if this message resulted in one
    related_draft = models.ForeignKey(
        RecipeDraftSuggestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    
    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
    
    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"[{self.role}] {preview}"

