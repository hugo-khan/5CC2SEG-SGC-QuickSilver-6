"""Minimal configuration helpers for AI service keys."""

import os

_PLACEHOLDER_VALUES = {
    "OPENAI_API_KEY",
    "SERPER_API_KEY",
    "PASTE_YOUR_OPENAI_API_KEY_HERE",
    "PASTE_YOUR_SERPER_API_KEY_HERE",
    "",
}

OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "OPENAI_API_KEY"
)

SERPER_API_KEY = os.environ.get(
    "SERPER_API_KEY",
    "SERPER_API_KEY"
)


def validate_keys():
    """Return (is_valid, errors) for the configured keys."""
    errors = []

    # Check if OPENAI_API_KEY is empty or still a placeholder
    if not OPENAI_API_KEY or OPENAI_API_KEY in _PLACEHOLDER_VALUES:
        errors.append("OPENAI_API_KEY is not configured")

    # Check if SERPER_API_KEY is empty or still a placeholder
    if not SERPER_API_KEY or SERPER_API_KEY in _PLACEHOLDER_VALUES:
        errors.append("SERPER_API_KEY is not configured")

    return len(errors) == 0, errors


def keys_configured():
    """Quick check if keys are configured."""
    is_valid, _ = validate_keys()
    return is_valid
