"""
Fast Recipe Service - Optimized AI recipe generation.

This module replaces the CrewAI multi-agent pipeline with a single LLM call
for dramatically improved response times (~10s vs ~40-45s).

Key optimizations:
1. Single LLM call (vs 2+ with CrewAI agents)
2. Direct Serper API with timeout and result limits
3. JSON-only output with capped lengths
4. Django cache for both search and LLM results

Usage:
    from recipes.ai.fast_recipe_service import suggest_recipe
    
    result = suggest_recipe("chicken pasta", dietary="gluten-free")
    # result = {
    #     "display_text": "...",
    #     "form_fields": {...},
    #     "raw_json": {...},
    #     "metadata": {"timing_ms": ..., "cache_hit": False, ...}
    # }
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

import requests
from django.conf import settings
from django.core.cache import cache

from recipes.ai.config import OPENAI_API_KEY, SERPER_API_KEY, keys_configured
from recipes.ai.profiling import (
    profile_stage, clear_profile, get_profile_summary, 
    start_wall_clock, increment_counter, log_profile_table
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class FastRecipeConfig:
    """Configuration for the fast recipe service. All values are tunable."""
    
    # Serper settings
    SERPER_TIMEOUT_SECONDS: float = 4.0  # Aggressive timeout
    SERPER_MAX_RESULTS: int = 3  # Only top 3 snippets
    SERPER_ENABLED: bool = True  # Can disable to skip retrieval entirely
    
    # LLM settings
    LLM_MODEL: str = "gpt-4o-mini"  # Fast, cheap model
    LLM_MAX_TOKENS: int = 1200  # Reduced from default
    LLM_TEMPERATURE: float = 0.7  # Slight creativity
    LLM_TIMEOUT_SECONDS: float = 30.0  # OpenAI timeout
    
    # Output caps
    MAX_INGREDIENTS: int = 12
    MAX_STEPS: int = 10
    MAX_SUMMARY_CHARS: int = 200
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 86400 * 3  # 3 days
    CACHE_PREFIX: str = "fast_recipe"


# Global config instance (can be modified for testing)
config = FastRecipeConfig()


# =============================================================================
# Exceptions
# =============================================================================

class FastRecipeError(Exception):
    """Base exception for fast recipe service."""
    pass


class SerperTimeoutError(FastRecipeError):
    """Raised when Serper search times out."""
    pass


class LLMError(FastRecipeError):
    """Raised when LLM call fails."""
    pass


# =============================================================================
# Caching Utilities
# =============================================================================

def _make_cache_key(prefix: str, *args: str) -> str:
    """Create a deterministic cache key from arguments."""
    content = "|".join(str(a).lower().strip() for a in args)
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"{config.CACHE_PREFIX}:{prefix}:{hash_val}"


def _get_cached(key: str) -> Optional[Dict]:
    """Get value from cache if enabled."""
    if not config.CACHE_ENABLED:
        return None
    try:
        return cache.get(key)
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
        return None


def _set_cached(key: str, value: Dict) -> None:
    """Set value in cache if enabled."""
    if not config.CACHE_ENABLED:
        return
    try:
        cache.set(key, value, config.CACHE_TTL_SECONDS)
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")


# =============================================================================
# Serper Search (Fast Path)
# =============================================================================

def search_recipes_serper(query: str) -> Tuple[str, bool]:
    """
    Search for recipe information using Serper API.
    
    Returns:
        Tuple of (search_context_string, success_bool)
        
    On timeout or error, returns a fallback message and False.
    """
    if not config.SERPER_ENABLED:
        logger.debug("Serper disabled, skipping search")
        return "", False
    
    cache_key = _make_cache_key("serper", query)
    cached = _get_cached(cache_key)
    if cached:
        logger.debug(f"Serper cache hit for: {query[:30]}...")
        increment_counter("cache_hits")
        return cached.get("context", ""), True
    
    increment_counter("cache_misses")
    increment_counter("serper_calls")
    
    with profile_stage("serper_api_call", {"query": query[:50], "timeout": config.SERPER_TIMEOUT_SECONDS}):
        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "q": f"recipe {query}",
                    "num": config.SERPER_MAX_RESULTS,
                },
                timeout=config.SERPER_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract only snippets (no page fetching)
            snippets = []
            for item in data.get("organic", [])[:config.SERPER_MAX_RESULTS]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                if snippet:
                    snippets.append(f"- {title}: {snippet}")
            
            context = "\n".join(snippets) if snippets else ""
            
            # Cache the result
            _set_cached(cache_key, {"context": context})
            
            logger.debug(f"Serper returned {len(snippets)} results")
            return context, True
            
        except requests.Timeout:
            logger.warning(f"Serper timeout after {config.SERPER_TIMEOUT_SECONDS}s for: {query[:50]}")
            increment_counter("errors")
            return "Search timed out - generating recipe from AI knowledge only.", False
            
        except requests.RequestException as e:
            logger.warning(f"Serper request failed: {e}")
            increment_counter("errors")
            return f"Search unavailable - generating recipe from AI knowledge only.", False
            
        except Exception as e:
            logger.error(f"Unexpected Serper error: {e}")
            increment_counter("errors")
            return "Search error - generating recipe from AI knowledge only.", False


# =============================================================================
# LLM Call (Single Call)
# =============================================================================

def _build_recipe_prompt(
    user_prompt: str,
    dietary: str,
    search_context: str,
    used_search: bool
) -> str:
    """Build the optimized prompt for single-call recipe generation."""
    
    dietary_note = f"\nDietary requirements: {dietary}" if dietary else ""
    
    search_section = ""
    if used_search and search_context:
        search_section = f"""
Web search results for reference (use as inspiration, not verbatim):
{search_context}
"""
    elif not used_search:
        search_section = "\n(No web search available - use your culinary knowledge)\n"
    
    return f"""You are a professional chef assistant. Create a recipe based on the user's request.

User request: "{user_prompt}"{dietary_note}
{search_section}
Output ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
    "title": "Recipe Title (max 200 chars)",
    "summary": "Brief 2-3 sentence description (max 200 chars)",
    "ingredients": [
        "quantity ingredient - optional notes"
    ],
    "instructions": [
        "Step 1: instruction",
        "Step 2: instruction"
    ],
    "prep_time_minutes": <integer - CALCULATE based on actual prep work needed>,
    "cook_time_minutes": <integer - CALCULATE based on actual cooking/baking time>,
    "servings": <integer - CALCULATE appropriate portion count>,
    "dietary_notes": "Any relevant dietary info"
}}

CRITICAL REQUIREMENTS:
- prep_time_minutes: Calculate REALISTIC prep time (chopping, mixing, marinating). Quick dishes ~5-10 min, complex dishes ~30-60 min.
- cook_time_minutes: Calculate REALISTIC cooking time based on method. Stir-fry ~10 min, roasting ~45-90 min, slow cooking ~2-8 hours (convert to minutes).
- servings: Estimate appropriate servings (typically 2-6 for home cooking, varies by dish type).
- Maximum {config.MAX_INGREDIENTS} ingredients
- Maximum {config.MAX_STEPS} steps
- Keep summary under {config.MAX_SUMMARY_CHARS} characters
- Include allergy warnings if relevant

DO NOT use placeholder values. Calculate each time/serving based on the specific recipe."""


def _call_openai(prompt: str) -> Dict:
    """
    Make a single OpenAI API call and return parsed JSON.
    
    Uses the requests library directly for simplicity and control.
    """
    increment_counter("llm_calls")
    
    with profile_stage("llm_api_call", {
        "model": config.LLM_MODEL, 
        "max_tokens": config.LLM_MAX_TOKENS,
        "timeout": config.LLM_TIMEOUT_SECONDS
    }):
        try:
            logger.debug(f"Calling OpenAI with model={config.LLM_MODEL}, max_tokens={config.LLM_MAX_TOKENS}")
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a professional chef. Output only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": config.LLM_MAX_TOKENS,
                    "temperature": config.LLM_TEMPERATURE,
                    "response_format": {"type": "json_object"},  # Force JSON mode
                },
                timeout=config.LLM_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Log token usage if available
            usage = data.get("usage", {})
            if usage:
                logger.debug(f"Token usage: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")
            
            # Parse JSON response
            return json.loads(content)
            
        except requests.Timeout:
            increment_counter("errors")
            raise LLMError(f"OpenAI request timed out after {config.LLM_TIMEOUT_SECONDS}s. Please try again.")
        except requests.RequestException as e:
            increment_counter("errors")
            raise LLMError(f"OpenAI request failed: {str(e)}")
        except json.JSONDecodeError as e:
            increment_counter("errors")
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise LLMError("Failed to parse recipe data from AI response.")
        except KeyError as e:
            increment_counter("errors")
            raise LLMError(f"Unexpected OpenAI response format: {e}")


# =============================================================================
# Formatting (Pure Python - No LLM)
# =============================================================================

def _format_display_text(recipe_json: Dict) -> str:
    """
    Format recipe JSON into a human-readable display string.
    This is pure Python - no LLM call needed.
    """
    title = recipe_json.get("title", "Recipe")
    summary = recipe_json.get("summary", "")
    ingredients = recipe_json.get("ingredients", [])
    instructions = recipe_json.get("instructions", [])
    prep_time = recipe_json.get("prep_time_minutes")
    cook_time = recipe_json.get("cook_time_minutes")
    servings = recipe_json.get("servings")
    dietary = recipe_json.get("dietary_notes", "")
    
    lines = [f"🍳 **{title}**", ""]
    
    if summary:
        lines.extend([summary, ""])
    
    # Time info
    time_parts = []
    if prep_time:
        time_parts.append(f"Prep: {prep_time} min")
    if cook_time:
        time_parts.append(f"Cook: {cook_time} min")
    if servings:
        time_parts.append(f"Serves: {servings}")
    if time_parts:
        lines.extend([" | ".join(time_parts), ""])
    
    # Ingredients
    if ingredients:
        lines.append("**Ingredients:**")
        for ing in ingredients[:config.MAX_INGREDIENTS]:
            lines.append(f"• {ing}")
        lines.append("")
    
    # Instructions
    if instructions:
        lines.append("**Instructions:**")
        for i, step in enumerate(instructions[:config.MAX_STEPS], 1):
            # Remove "Step N:" prefix if already present
            step_text = step
            if step.lower().startswith(f"step {i}:"):
                step_text = step[len(f"step {i}:"):].strip()
            elif step.lower().startswith(f"step {i}."):
                step_text = step[len(f"step {i}."):].strip()
            lines.append(f"{i}. {step_text}")
        lines.append("")
    
    # Dietary notes
    if dietary:
        lines.append(f"📝 {dietary}")
    
    return "\n".join(lines)


def _format_form_fields(recipe_json: Dict) -> Dict:
    """
    Convert recipe JSON to Django form field format.
    This is pure Python - no LLM call needed.
    """
    ingredients = recipe_json.get("ingredients", [])
    instructions = recipe_json.get("instructions", [])
    
    # Format ingredients as newline-separated string
    ingredients_str = "\n".join(ingredients[:config.MAX_INGREDIENTS])
    
    # Format instructions as newline-separated string
    instructions_str = "\n".join(instructions[:config.MAX_STEPS])
    
    return {
        "title": recipe_json.get("title", "Untitled Recipe")[:200],
        "summary": recipe_json.get("summary", "")[:255],
        "ingredients": ingredients_str,
        "instructions": instructions_str,
        "prep_time_minutes": recipe_json.get("prep_time_minutes"),
        "cook_time_minutes": recipe_json.get("cook_time_minutes"),
        "servings": recipe_json.get("servings"),
    }


# =============================================================================
# Main Entry Point
# =============================================================================

def suggest_recipe(
    prompt: str,
    dietary: str = "",
    skip_cache: bool = False,
) -> Dict[str, Any]:
    """
    Generate a recipe suggestion with optimized performance.
    
    Args:
        prompt: User's recipe request
        dietary: Optional dietary requirements
        skip_cache: If True, bypass cache (for testing)
    
    Returns:
        Dict with keys:
            - display_text: Formatted text for chat display
            - form_fields: Dict matching Django Recipe form fields
            - raw_json: The raw recipe JSON from LLM
            - metadata: Dict with timing, cache_hit, used_retrieval, etc.
    
    Raises:
        FastRecipeError: If API keys not configured or LLM fails
    """
    # Initialize profiling
    clear_profile()
    start_wall_clock()
    start_time = time.perf_counter()
    
    logger.info(f"[FAST RECIPE] Starting suggestion for: {prompt[:50]}...")
    
    # Validate API keys
    if not keys_configured():
        raise FastRecipeError(
            "API keys are not configured. Please set OPENAI_API_KEY and SERPER_API_KEY "
            "in your environment or in recipes/ai/config.py"
        )
    
    # Check cache for full result
    cache_key = _make_cache_key("recipe", prompt, dietary)
    if not skip_cache:
        with profile_stage("cache_check"):
            cached = _get_cached(cache_key)
        if cached:
            increment_counter("cache_hits")
            total_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"[FAST RECIPE] Cache hit! Returned in {total_time_ms:.0f}ms")
            cached["metadata"]["cache_hit"] = True
            cached["metadata"]["timing_ms"] = round(total_time_ms, 1)
            return cached
    
    increment_counter("cache_misses")
    
    # Step 1: Search (with timeout fallback)
    with profile_stage("search_total"):
        search_context, used_retrieval = search_recipes_serper(prompt)
    
    # Step 2: Build prompt and call LLM (single call)
    with profile_stage("prompt_build"):
        llm_prompt = _build_recipe_prompt(prompt, dietary, search_context, used_retrieval)
    
    with profile_stage("llm_total"):
        recipe_json = _call_openai(llm_prompt)
    
    # Step 3: Format outputs (pure Python, fast)
    with profile_stage("formatting"):
        display_text = _format_display_text(recipe_json)
        form_fields = _format_form_fields(recipe_json)
    
    # Build result
    total_time_ms = (time.perf_counter() - start_time) * 1000
    profile_summary = get_profile_summary()
    
    result = {
        "display_text": display_text,
        "form_fields": form_fields,
        "raw_json": recipe_json,
        "metadata": {
            "timing_ms": round(total_time_ms, 1),
            "cache_hit": False,
            "used_retrieval": used_retrieval,
            "profile": profile_summary,
        },
    }
    
    # Cache the result
    if not skip_cache:
        with profile_stage("cache_write"):
            _set_cached(cache_key, result)
    
    # Log performance summary
    if getattr(settings, 'DEBUG', False):
        logger.info(log_profile_table())
        logger.info(
            f"[FAST RECIPE] Generated in {total_time_ms:.0f}ms "
            f"(retrieval={'yes' if used_retrieval else 'no'}, cache=no, "
            f"llm_calls={profile_summary.get('counters', {}).get('llm_calls', 0)})"
        )
    
    return result


# =============================================================================
# Publishing (Pure Python - No LLM)
# =============================================================================

def publish_recipe_from_fields(form_fields: Dict, user) -> "Recipe":
    """
    Publish a recipe from form fields to the database.
    
    This is pure Python validation + DB write. No LLM call.
    
    Args:
        form_fields: Dict with recipe data (from suggest_recipe)
        user: Django User instance
    
    Returns:
        Created Recipe instance
    
    Raises:
        FastRecipeError: If validation fails
    """
    from recipes.models import Recipe
    
    with profile_stage("db_write"):
        # Validate required fields
        required = ["title", "ingredients", "instructions"]
        missing = [f for f in required if not form_fields.get(f)]
        if missing:
            raise FastRecipeError(f"Missing required fields: {', '.join(missing)}")
        
        # Create recipe
        recipe = Recipe.objects.create(
            author=user,
            title=form_fields.get("title", "Untitled Recipe"),
            summary=form_fields.get("summary", ""),
            name=form_fields.get("title", "Untitled Recipe"),
            description=form_fields.get("summary", ""),
            ingredients=form_fields.get("ingredients", ""),
            instructions=form_fields.get("instructions", ""),
            prep_time_minutes=form_fields.get("prep_time_minutes"),
            cook_time_minutes=form_fields.get("cook_time_minutes"),
            servings=form_fields.get("servings"),
            is_published=True,
        )
        
        return recipe

