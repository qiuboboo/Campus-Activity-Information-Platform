"""AI Service — lightweight LLM integration for activity extraction and enrichment.

Design principles:
- Model-agnostic: works with any OpenAI-compatible API (DeepSeek, OpenAI, Claude via proxy, etc.)
- Zero extra SDK dependencies: uses only ``requests`` (already in requirements.txt)
- Graceful degradation: returns empty/fallback results when LLM is unavailable
- Configurable via ``current_app.config`` (LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unified LLM client
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 2
_RETRY_DELAY = 1.0


def _get_config(key: str, default: Any = None) -> Any:
    """Read config from Flask app context if available, else os.environ."""
    try:
        from flask import current_app

        return current_app.config.get(key, default)
    except (RuntimeError, ImportError):
        import os

        return os.getenv(key, default)


def _resolve_profile(profile: str | None) -> dict:
    """Resolve API credentials from *profile* name, falling back to default config."""
    if profile:
        try:
            from .model_manager import get_profile

            cfg = get_profile(profile)
            if cfg is not None:
                return {
                    "key": cfg["key"],
                    "base_url": cfg.get("base_url", "https://api.deepseek.com").rstrip("/"),
                    "model": cfg.get("model", "deepseek-chat"),
                }
            logger.warning("Profile '%s' not found, falling back to default", profile)
        except Exception:
            logger.exception("Error resolving profile '%s', falling back to default", profile)

    return {
        "key": _get_config("LLM_API_KEY", ""),
        "base_url": _get_config("LLM_API_BASE_URL", "https://api.deepseek.com").rstrip("/"),
        "model": _get_config("LLM_MODEL", "deepseek-chat"),
    }


def _llm_chat(
    messages: list[dict],
    *,
    response_format: type | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
    profile: str | None = None,
) -> dict | None:
    """Call the configured LLM API with *messages*.

    When *profile* is given, resolves API credentials from the named
    model profile (``model_manager.get_profile``).  Falls back to the
    default ``LLM_API_KEY / LLM_API_BASE_URL / LLM_MODEL`` config.

    Returns the parsed JSON response body on success, or ``None`` if the call
    fails after retries.  Logs errors but never raises.
    """
    resolved = _resolve_profile(profile)
    api_key = resolved["key"]
    if not api_key:
        logger.warning("LLM_API_KEY is not set — skipping LLM call")
        return None

    base_url = resolved["base_url"]
    model = resolved["model"]

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,  # low temperature for deterministic extraction
    }
    if response_format is not None:
        body["response_format"] = {"type": "json_object"}

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            # Try parsing as JSON if response_format was requested
            if response_format is not None:
                return json.loads(content)
            return {"content": content, "model": model}
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            last_error = e
            logger.warning("LLM call attempt %d/%d failed: %s", attempt + 1, _MAX_RETRIES + 1, e)
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)

    logger.error("LLM call failed after %d retries: %s", _MAX_RETRIES + 1, last_error)
    return None


# ---------------------------------------------------------------------------
# Activity extraction
# ---------------------------------------------------------------------------

_EXTRACT_SYSTEM_PROMPT = """你是一个校园活动信息提取助手。从用户提供的活动文本中提取结构化信息。

请返回 JSON 对象，包含以下字段（没有找到的字段设为 null）：
- title: 活动标题
- event_time: 活动时间（ISO 8601 格式，如 "2026-05-10T19:00:00"）
- location: 活动地点
- organizer: 主办方/组织者
- summary: 活动简介（不超过 200 字）
- tags: 活动标签数组，如 ["讲座", "科技", "学术"]
- activity_type: 活动类型（讲座/晚会/竞赛/论坛/展览/招聘/体育/其他）

只返回 JSON，不要包含其他文字。"""


def extract_from_text(raw_text: str, profile: str | None = None) -> dict:
    """Extract structured activity fields from *raw_text* using LLM.

    Optionally specify a *profile* name (e.g. ``"copilot"``) to use a
    non-default LLM configuration.

    Falls back to rule-based extraction when the LLM is unavailable.
    """
    if not raw_text or not raw_text.strip():
        return {}

    result = _llm_chat(
        [
            {"role": "system", "content": _EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": raw_text[:4000]},  # truncate to avoid token limits
        ],
        response_format=dict,
        profile=profile,
    )

    if result is None:
        logger.info("LLM extraction failed — falling back to rule-based extractor")
        from .fallback_extractor import fallback_extract

        result = fallback_extract(raw_text)
        result["_fallback"] = True
        return result

    # Normalise event_time to datetime if present
    if isinstance(result.get("event_time"), str):
        try:
            result["event_time"] = datetime.fromisoformat(result["event_time"])
        except (ValueError, TypeError):
            result["event_time"] = None

    return result


# ---------------------------------------------------------------------------
# Poster enrichment
# ---------------------------------------------------------------------------

_ENRICH_SYSTEM_PROMPT = """你是一个校园活动信息增强助手。对已有的活动海报信息进行补充和完善。

请返回 JSON 对象，包含以下字段：
- summary: 活动简介（不超过 150 字）
- tags: 活动标签数组
- activity_type: 活动类型
- keywords: 关键词数组（3-5 个）
- related_suggestions: 建议关联的知识节点名称数组

只返回 JSON，不要包含其他文字。"""


def enrich_poster(poster_id: int) -> dict:
    """Enrich a poster with AI-generated summary, tags, and keywords.

    Reads the poster from the database, calls LLM, and updates the record.
    Gracefully handles missing poster or LLM failure.
    """
    from ..extensions import db
    from ..models import Poster

    poster = db.session.get(Poster, poster_id)
    if poster is None:
        logger.warning("enrich_poster: poster %d not found", poster_id)
        return {}

    input_text = f"标题：{poster.title}\n内容：{poster.raw_text[:3000]}"
    if poster.location:
        input_text += f"\n地点：{poster.location}"
    if poster.organizer:
        input_text += f"\n主办方：{poster.organizer}"

    result = _llm_chat(
        [
            {"role": "system", "content": _ENRICH_SYSTEM_PROMPT},
            {"role": "user", "content": input_text},
        ],
        response_format=dict,
    )

    if result is None:
        return {}

    # Update poster fields
    changed = False
    if result.get("summary") and not poster.summary:
        poster.summary = result["summary"][:500]
        changed = True
    if result.get("tags"):
        existing = getattr(poster, "tags", None)
        if not existing:
            poster.tags = ",".join(result["tags"][:10])
            changed = True
    if result.get("activity_type"):
        poster.activity_type = result["activity_type"]
        changed = True

    if changed:
        db.session.commit()

    return result


# ---------------------------------------------------------------------------
# External search (LLM-driven)
# ---------------------------------------------------------------------------


def search_external(query: str, sources: list[str] | None = None) -> dict:
    """Search for activity information using LLM knowledge.

    This is a lightweight alternative to full web search — it relies on the
    LLM's training data. For real-time search, connect a search MCP server.

    Returns a dict with:
        results (list[dict]):  list of result dicts with keys: title, summary, source, url
        error (str | None):    error message if the call failed, None on success
    """
    # Check API key upfront so we can give a clear error
    if not _get_config("LLM_API_KEY", ""):
        logger.error("External search failed: LLM_API_KEY is not set")
        return {"results": [], "error": "LLM service not configured"}

    sources_str = ", ".join(sources) if sources else "校园网站、社交媒体、活动平台"
    prompt = (
        f"搜索以下校园活动信息，请从以下来源查找：{sources_str}\n\n"
        f"查询：{query}\n\n"
        f"请返回 JSON 数组，每个元素包含 title、summary、source、url 字段。"
        f"如果搜索结果为空，返回空数组。只返回 JSON。"
    )

    result = _llm_chat(
        [
            {"role": "system", "content": "你是一个校园活动搜索助手。返回 JSON 数组。"},
            {"role": "user", "content": prompt},
        ],
        response_format=list,
    )

    if result is None:
        logger.error("External search failed: LLM call returned None after retries")
        return {"results": [], "error": "LLM service unavailable"}

    if not isinstance(result, list):
        logger.warning(
            "External search returned unexpected type (expected list, got %s): %r",
            type(result).__name__,
            result,
        )
        return {"results": [], "error": "LLM returned invalid response format"}

    return {"results": result, "error": None}
