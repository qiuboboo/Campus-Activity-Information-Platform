"""Model Manager — multi-LLM profile discovery and dispatch.

Provides a single entry point for resolving named model profiles
(e.g. "default", "deepseek", "copilot") into API credentials.

Usage::

    from .model_manager import list_profiles, get_profile

    all_profiles = list_profiles()
    profile = get_profile("copilot")  # -> {"key": ..., "base_url": ..., "model": ...}
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def list_profiles() -> dict[str, dict]:
    """Discover all configured LLM profiles.

    Delegates to ``Config.list_llm_profiles()`` which reads from
    environment variables.  Works with or without a Flask app context.
    """
    # Import is deferred to avoid circular imports at module level
    from ..config import Config

    return Config.list_llm_profiles()


def get_profile(name: str = "default") -> dict[str, Any] | None:
    """Get a single LLM profile by *name*.

    Returns ``None`` when the profile is not configured.
    """
    profiles = list_profiles()
    if name not in profiles:
        logger.warning("LLM profile '%s' not found among: %s", name, list(profiles.keys()))
        return None
    return profiles[name]
