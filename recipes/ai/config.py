"""
Configuration for AI services.

API Keys Configuration:
-----------------------
You can set these keys in two ways:

1. Environment variables (recommended for production):
   Set OPENAI_API_KEY and SERPER_API_KEY in your environment or .env file

2. Direct paste (for quick testing only - DO NOT COMMIT real keys):
   Replace the placeholder strings below with your actual keys

Usage:
    from recipes.ai.config import OPENAI_API_KEY, SERPER_API_KEY
"""

import os

# =============================================================================
# OPENAI API KEY
# -----------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "OPENAI_API_KEY" # replace with your key
)

# =============================================================================
# SERPER API KEY (for web search / RAG)
# -----------------------------------------------------------------------------
SERPER_API_KEY = os.environ.get(
    "SERPER_API_KEY",
    "SERPER_API_KEY" # replace with your key
)


def validate_keys():
    """
    Check if API keys are properly configured.
    Returns a tuple of (is_valid, error_messages).
    """
    errors = []
    
    # Check if OPENAI_API_KEY is empty or still a placeholder
    if not OPENAI_API_KEY or OPENAI_API_KEY == "PASTE_YOUR_OPENAI_API_KEY_HERE":
        errors.append("OPENAI_API_KEY is not configured")
    
    # Check if SERPER_API_KEY is empty or still a placeholder
    if not SERPER_API_KEY or SERPER_API_KEY == "PASTE_YOUR_SERPER_API_KEY_HERE":
        errors.append("SERPER_API_KEY is not configured")
    
    return len(errors) == 0, errors


def keys_configured():
    """Quick check if keys are configured."""
    is_valid, _ = validate_keys()
    return is_valid

