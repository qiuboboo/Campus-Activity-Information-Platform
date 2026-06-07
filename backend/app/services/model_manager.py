"""Model Manager — multi-LLM profile discovery and dispatch.

Discovers LLM profiles from environment variables (``LLM_API_KEY`` for
the default profile, ``LLM_{NAME}_KEY`` / ``LLM_{NAME}_BASE_URL`` /
``LLM_{NAME}_MODEL`` for named profiles).

Usage::

    from .model_manager import list_profiles, get_profile

    all_profiles = list_profiles()
    profile = get_profile("copilot")  # -> {"key": ..., "base_url": ..., "model": ...}
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def list_profiles() -> dict[str, dict]:
    """Discover all configured LLM profiles from environment variables.

    Returns a dict keyed by profile name, each containing key/base_url/model.
    The ``"default"`` profile is always present if LLM_API_KEY is set.
    """
    profiles: dict[str, dict] = {}

    key = os.getenv("LLM_API_KEY", "")
    if key:
        profiles["default"] = {
            "key": key,
            "base_url": os.getenv("LLM_API_BASE_URL", "https://api.deepseek.com"),
            "model": os.getenv("LLM_MODEL", "deepseek-chat"),
        }

    for env_key, env_val in sorted(os.environ.items()):
        if not env_val:
            continue
        if env_key.startswith("LLM_") and env_key.endswith("_KEY"):
            name = env_key[4:-4].lower()
            if name == "api":
                continue
            prefix = f"LLM_{name.upper()}"
            profiles[name] = {
                "key": env_val,
                "base_url": os.getenv(f"{prefix}_BASE_URL", "https://api.deepseek.com"),
                "model": os.getenv(f"{prefix}_MODEL", ""),
            }

    return profiles


def get_profile(name: str = "default") -> dict[str, Any] | None:
    """Get a single LLM profile by *name*.

    Returns ``None`` when the profile is not configured.
    """
    profiles = list_profiles()
    if name not in profiles:
        logger.warning("LLM profile '%s' not found among: %s", name, list(profiles.keys()))
        return None
    return profiles[name]
