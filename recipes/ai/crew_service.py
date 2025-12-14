"""Legacy CrewAI workflow for recipe suggestions (kept for compatibility)."""

import json
import logging
from typing import Any

from django.utils.text import slugify

from recipes.ai.profiling import clear_profile, log_profile_table, profile_stage

logger = logging.getLogger(__name__)

# Lazy imports for crewai to allow migrations without the package installed
_crewai_available = None


def _check_crewai():
    """Check if crewai is available and import it lazily."""
    global _crewai_available
    if _crewai_available is None:
        try:
            from crewai import Agent, Crew, Process, Task
            from crewai.tools import tool
            from crewai_tools import SerperDevTool

            _crewai_available = True
        except ImportError:
            _crewai_available = False
    return _crewai_available


def _get_crewai_components():
    """Get crewai components, raising ImportError if not available."""
    if not _check_crewai():
        raise ImportError(
            "crewai is not installed. Please install it with: pip install crewai crewai-tools"
        )
    from crewai import Agent, Crew, Process, Task
    from crewai.tools import tool
    from crewai_tools import SerperDevTool

    return Agent, Task, Crew, Process, tool, SerperDevTool


# Build a Serper-backed web search tool for recipe lookups
def _create_recipe_web_search_tool():
    """Create the recipe web search tool using crewai decorators."""
    from recipes.ai.config import SERPER_API_KEY

    _, _, _, _, tool, SerperDevTool = _get_crewai_components()

    @tool("recipe_web_search")
    def recipe_web_search(query: str) -> str:
        """
        Search the web for recipe information using Serper API.
        Use this to find recipe ideas, ingredients, and cooking instructions.
        """
        with profile_stage("serper_search", {"query": query[:50]}):
            try:
                serper_tool = SerperDevTool(api_key=SERPER_API_KEY)
                results = serper_tool.run(search_query=query)
                return results
            except Exception as e:
                logger.error(f"Serper search failed: {e}")
                return f"Search failed: {str(e)}"

    return recipe_web_search


# Agent that performs recipe research with RAG
def create_recipe_researcher():
    """Create the researcher agent used for RAG lookups."""
    Agent, _, _, _, _, _ = _get_crewai_components()
    recipe_web_search = _create_recipe_web_search_tool()

    return Agent(
        role="Recipe Research & Culinary Planner",
        goal=(
            "Retrieve relevant recipe sources using web search and synthesize "
            "a coherent, complete recipe that meets the user's dietary constraints "
            "and preferences. Provide accurate ingredient quantities and clear instructions."
        ),
        backstory=(
            "You are a seasoned test-kitchen researcher with 15 years of experience "
            "developing recipes for major food publications. You prioritize reliability, "
            "clarity, and food safety in every recipe. You're skilled at finding the best "
            "recipe sources online and combining techniques from multiple sources into "
            "a single optimized recipe. You always note potential ingredient substitutions "
            "for common dietary restrictions."
        ),
        tools=[recipe_web_search],
        verbose=True,
        allow_delegation=False,
    )


# Agent that formats recipe output for chat and forms
def create_formatter_agent():
    """Create the formatting agent that rewrites the recipe output."""
    Agent, _, _, _, _, _ = _get_crewai_components()

    return Agent(
        role="Cookbook Editor & UX Writer",
        goal=(
            "Convert structured recipe JSON into two outputs: "
            "(1) a polished, readable chat response for the user, and "
            "(2) a Django-form-ready dictionary with exact field mappings. "
            "Ensure consistent formatting, readable step numbering, and proper structure."
        ),
        backstory=(
            "You are an experienced cookbook editor who has worked on over 50 published "
            "cookbooks. You understand how to present recipes clearly, with proper "
            "ingredient formatting, numbered steps, and helpful tips. You also have "
            "technical expertise in mapping recipe data to web form fields, ensuring "
            "data integrity between the AI output and the application's database schema."
        ),
        verbose=True,
        allow_delegation=False,
    )


# Agent that validates and publishes recipes
def create_publisher_agent():
    """Create the agent that validates and publishes recipes."""
    Agent, _, _, _, _, _ = _get_crewai_components()

    return Agent(
        role="Publishing Assistant",
        goal=(
            "Validate recipe data completeness and publish to the database only when "
            "explicitly requested by the user. Never publish without clear instruction. "
            "Prevent duplicate recipes and ensure all required fields are present."
        ),
        backstory=(
            "You are a careful editorial assistant with a strong attention to detail. "
            "You never publish content without explicit approval. You check for duplicates, "
            "validate that all required recipe fields are present and properly formatted, "
            "and ensure the recipe meets quality standards before publishing. You always "
            "confirm actions with clear success or failure messages."
        ),
        verbose=True,
        allow_delegation=False,
    )


# Task for researching and drafting a recipe
def create_research_task(prompt: str, dietary_requirements: str, researcher):
    """Create the recipe research task."""
    _, Task, _, _, _, _ = _get_crewai_components()

    dietary_note = (
        f"Dietary requirements: {dietary_requirements}"
        if dietary_requirements
        else "No specific dietary requirements."
    )

    return Task(
        description=f"""
Research and create a complete recipe based on the user's request.

User prompt: "{prompt}"
{dietary_note}

You MUST:
1. Search the web for relevant recipe information and sources
2. Synthesize findings into a complete, coherent recipe
3. Include accurate ingredient quantities with notes for substitutions
4. Provide clear, numbered cooking instructions
5. Note any dietary considerations or allergen warnings

Output MUST be valid JSON with this exact structure:
{{
    "title": "Recipe Title",
    "summary": "Brief 1-2 sentence description",
    "ingredients": [
        {{"item": "ingredient name", "quantity": "amount with unit", "notes": "optional notes"}}
    ],
    "instructions": [
        "Step 1: ...",
        "Step 2: ..."
    ],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45,
    "servings": 4,
    "dietary_notes": "Relevant dietary information",
    "sources": [
        {{"title": "Source Name", "url": "https://..."}}
    ]
}}
""",
        expected_output="Valid JSON object with the complete recipe structure as specified.",
        agent=researcher,
    )


# Task for formatting the recipe output
def create_format_task(formatter):
    """Create the formatting task."""
    _, Task, _, _, _, _ = _get_crewai_components()

    return Task(
        description="""
Take the structured recipe JSON from the previous task and create two outputs:

1. assistant_display: A beautifully formatted text response for the chat interface.
   Include:
   - Recipe title as a header
   - Brief description
   - Ingredients list (formatted nicely)
   - Numbered cooking steps
   - Time and serving information
   - Any dietary notes
   - Sources cited

2. form_fields: A dictionary matching the exact Django Recipe form fields:
   - title: string (max 200 chars)
   - summary: string (max 255 chars)
   - ingredients: string (ingredients separated by newlines, format: "quantity item - notes")
   - instructions: string (steps separated by newlines)
   - prep_time_minutes: integer or null
   - cook_time_minutes: integer or null
   - servings: integer or null
   - dietary_requirement: one of [vegan, vegetarian, gluten_free, dairy_free, nut_free, none]
   - difficulty: one of [easy, medium, hard]

Output MUST be valid JSON with this structure:
{
    "assistant_display": "Your formatted chat message here...",
    "form_fields": {
        "title": "...",
        "summary": "...",
        "ingredients": "...",
        "instructions": "...",
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "servings": 4,
        "dietary_requirement": "vegan",
        "difficulty": "medium"
    }
}
""",
        expected_output="Valid JSON with assistant_display string and form_fields dictionary.",
        agent=formatter,
    )


class CrewServiceError(Exception):
    """Custom exception for crew service errors."""

    pass


def run_suggestion(prompt: str, dietary_requirements: str = "") -> dict[str, Any]:
    """Run the CrewAI suggestion workflow and return display/form payloads."""
    import os

    from django.conf import settings

    from recipes.ai.config import OPENAI_API_KEY, SERPER_API_KEY, keys_configured

    # Clear any previous profiling data
    clear_profile()

    if not keys_configured():
        raise CrewServiceError(
            "API keys are not configured. Please set OPENAI_API_KEY and SERPER_API_KEY "
            "in your environment or in recipes/ai/config.py"
        )

    # Set environment variables for CrewAI/litellm to pick up
    # This is necessary because litellm reads directly from os.environ
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["SERPER_API_KEY"] = SERPER_API_KEY

    try:
        with profile_stage("crew_setup"):
            # Get crewai components
            _, _, Crew, Process, _, _ = _get_crewai_components()

            # Create agents
            researcher = create_recipe_researcher()
            formatter = create_formatter_agent()

            # Create tasks
            research_task = create_research_task(
                prompt, dietary_requirements, researcher
            )
            format_task = create_format_task(formatter)

            # Create crew
            crew = Crew(
                agents=[researcher, formatter],
                tasks=[research_task, format_task],
                process=Process.sequential,
                verbose=True,
            )

        with profile_stage("crew_kickoff_total"):
            result = crew.kickoff()

        with profile_stage("parse_output"):
            # Parse the result
            raw_output = str(result)

            # Try to extract JSON from the output
            parsed = _parse_crew_output(raw_output)

        # Log profiling summary
        if getattr(settings, "DEBUG", False):
            logger.info(log_profile_table())

        return {
            "assistant_display": parsed.get("assistant_display", raw_output),
            "form_fields": parsed.get("form_fields", {}),
            "raw": raw_output,
        }

    except ImportError as e:
        logger.error(f"CrewAI not available: {e}")
        raise CrewServiceError(
            "AI features are not available. CrewAI is not installed. "
            "Please run: pip install crewai crewai-tools"
        )
    except Exception as e:
        logger.error(f"Crew workflow failed: {e}")
        raise CrewServiceError(f"Failed to generate recipe suggestion: {str(e)}")


def _parse_crew_output(output: str) -> dict:
    """Parse CrewAI output into structured data or fall back to raw text."""
    # Try to find JSON in the output
    import re

    # Look for JSON block (possibly wrapped in markdown code blocks)
    json_patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r'\{[\s\S]*"assistant_display"[\s\S]*\}',
    ]

    for pattern in json_patterns:
        match = re.search(pattern, output, re.DOTALL)
        if match:
            try:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

    # If no valid JSON found, try to parse the entire output
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        # Return a basic structure with the raw output as display
        return {
            "assistant_display": output,
            "form_fields": {},
        }


def publish_from_draft(draft, user) -> dict[str, Any]:
    """Publish a draft to a Recipe instance if owned by the caller."""
    from django.urls import reverse

    from recipes.models import Recipe, RecipeDraftSuggestion

    # Validate ownership
    if draft.user != user:
        raise CrewServiceError("You can only publish your own drafts.")

    # Check draft status
    if draft.status == RecipeDraftSuggestion.Status.PUBLISHED:
        raise CrewServiceError("This recipe has already been published.")

    # Get form fields from draft
    form_fields = draft.draft_payload

    if not form_fields:
        raise CrewServiceError("Draft has no recipe data to publish.")

    # Validate required fields
    required_fields = ["title", "ingredients", "instructions"]
    missing = [f for f in required_fields if not form_fields.get(f)]
    if missing:
        raise CrewServiceError(f"Missing required fields: {', '.join(missing)}")

    dietary_requirement = form_fields.get("dietary_requirement") or "none"
    difficulty = form_fields.get("difficulty") or "easy"

    try:
        # Create the recipe
        recipe = Recipe.objects.create(
            author=user,
            title=form_fields.get("title", "Untitled Recipe"),
            summary=form_fields.get("summary", ""),
            name=form_fields.get(
                "title", "Untitled Recipe"
            ),  # Populate both naming conventions
            description=form_fields.get("summary", ""),
            ingredients=form_fields.get("ingredients", ""),
            instructions=form_fields.get("instructions", ""),
            prep_time_minutes=form_fields.get("prep_time_minutes"),
            cook_time_minutes=form_fields.get("cook_time_minutes"),
            servings=form_fields.get("servings"),
            dietary_requirement=dietary_requirement,
            difficulty=difficulty,
            is_published=True,
        )

        # Seed image (non-blocking)
        _seed_recipe_image(recipe)

        # Update draft status
        draft.status = RecipeDraftSuggestion.Status.PUBLISHED
        draft.published_recipe = recipe
        draft.save()

        recipe_url = reverse("recipe_detail", kwargs={"pk": recipe.pk})

        return {
            "recipe": recipe,
            "recipe_url": recipe_url,
        }

    except Exception as e:
        logger.error(f"Failed to publish recipe: {e}")
        draft.status = RecipeDraftSuggestion.Status.FAILED
        draft.save()
        raise CrewServiceError(f"Failed to publish recipe: {str(e)}")


def _seed_recipe_image(recipe):
    """Seed a recipe image using the populate_images command helpers."""
    try:
        from recipes.management.commands.populate_images import (
            Command as PopulateImagesCommand,
        )

        cmd = PopulateImagesCommand()
        image_url = cmd.get_pexels_image(recipe)

        basename = slugify(recipe.title) or f"recipe-{recipe.id}"
        image_file = cmd.download_image_to_file(image_url, basename)

        if not image_file:
            image_file = cmd.generate_placeholder_image(recipe.title, basename)

        if image_file:
            filename = f"{basename}.jpg"
            recipe.image.save(filename, image_file, save=False)
            recipe.image_url = image_url
            recipe.save(update_fields=["image", "image_url"])
    except Exception as exc:
        logger.exception(
            f"Image seeding failed for recipe {getattr(recipe, 'id', '?')}: {exc}"
        )
