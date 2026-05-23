"""Multi-engine search service — aggregates results from SearXNG and Sogou.

Architecture:
- SearXNG (self-hosted metasearch) → Google, Bing, DuckDuckGo, Baidu
- weixin_search_service → Sogou (WeChat article search)
- Results are aggregated, deduplicated, and returned in a standard format.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 20

# Map external engine names to SearXNG engine names
_SEARXNG_ENGINES = {
    "google",
    "bing",
    "duckduckgo",
    "baidu",
}

# Default set of engines to query
_DEFAULT_ENGINES = sorted(_SEARXNG_ENGINES)


def _get_searxng_base_url() -> str:
    """Get SearXNG base URL from Flask app config or environment."""
    try:
        from flask import current_app

        return current_app.config.get("SEARXNG_BASE_URL", "http://campus-activity-searxng:8080")
    except (RuntimeError, ImportError):
        import os

        return os.getenv("SEARXNG_BASE_URL", "http://campus-activity-searxng:8080")


def _search_searxng(query: str, engines: list[str] | None = None) -> list[dict]:
    """Query SearXNG metasearch and return raw results.

    Args:
        query: Search query string.
        engines: List of SearXNG engine names. Defaults to all configured engines.

    Returns:
        List of raw result dicts from SearXNG, or empty list on failure.
    """
    base_url = _get_searxng_base_url()
    if not engines:
        engines = _DEFAULT_ENGINES

    params: dict[str, Any] = {
        "q": query,
        "format": "json",
        "language": "zh-CN",
        "categories": "general",
        "pageno": 1,
    }
    if engines:
        params["engines"] = ",".join(engines)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CampusBot/1.0)",
        "X-Forwarded-For": "172.18.0.3",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/search",
            params=params,
            headers=headers,
            timeout=_REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning("SearXNG returned status %d for query: %s", resp.status_code, query)
            return []

        data = resp.json()
        return data.get("results", [])
    except requests.RequestException as e:
        logger.warning("SearXNG request failed: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("SearXNG response parse failed: %s", e)
        return []


def _normalise_result(
    raw: dict, engine: str | None = None
) -> dict:
    """Normalise a SearXNG result dict to our standard format.

    Standard format:
        title (str): Result title
        summary (str): Result snippet
        source (str): Engine name (e.g. "google", "baidu")
        url (str | None): Full URL to the source page
    """
    eng = raw.get("engine") or engine or "unknown"
    return {
        "title": (raw.get("title") or "").strip(),
        "summary": (raw.get("content") or "").strip(),
        "source": eng,
        "url": raw.get("url") or None,
    }


def _normalise_sogou_result(
    raw: dict,
) -> dict:
    """Normalise a Sogou/WeChat result dict to our standard format."""
    return {
        "title": (raw.get("title") or "").strip(),
        "summary": "",
        "source": "sogou",
        "url": raw.get("sogou_url") or None,
    }


def _deduplicate(results: list[dict]) -> list[dict]:
    """Remove duplicates by URL. Preserves order, keeps first occurrence."""
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in results:
        url = r.get("url") or ""
        key = url.strip().rstrip("/")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        deduped.append(r)
    return deduped


def search(
    query: str,
    engines: list[str] | None = None,
) -> dict:
    """Multi-engine search — aggregate results from SearXNG and Sogou.

    Args:
        query: Search query string.
        engines: Which engines to use. Values: "google", "bing", "duckduckgo",
                 "baidu", "sogou". If None, uses all available engines.

    Returns:
        Dict with keys:
            results (list[dict]): Standardised result list.
            error (str | None): Error message if all sources failed, else None.
    """
    if not query or not query.strip():
        return {"results": [], "error": None}

    if engines is None:
        engines = list(_DEFAULT_ENGINES) + ["sogou"]
    else:
        # Normalise engine names
        engines = [e.strip().lower() for e in engines]

    # Split into SearXNG engines and Sogou
    searxng_engines = [e for e in engines if e in _SEARXNG_ENGINES]
    use_sogou = "sogou" in engines

    all_results: list[dict] = []

    # 1. SearXNG search
    if searxng_engines:
        searxng_raw = _search_searxng(query, engines=searxng_engines)
        for r in searxng_raw:
            all_results.append(_normalise_result(r))
        logger.info(
            "SearXNG returned %d results for query=%r engines=%s",
            len(searxng_raw),
            query,
            searxng_engines,
        )

    # 2. Sogou search (lazy import — lxml may not be available)
    if use_sogou:
        try:
            from .weixin_search_service import sogou_search

            sogou_results = sogou_search(query, page=1)
            for r in sogou_results:
                all_results.append(_normalise_sogou_result(r))
            logger.info(
                "Sogou returned %d results for query=%r",
                len(sogou_results),
                query,
            )
        except Exception as e:
            logger.warning("Sogou search failed for query=%r: %s", query, e)

    # 3. Deduplicate
    all_results = _deduplicate(all_results)

    # Determine error status
    error = None
    if not all_results and not searxng_engines and not use_sogou:
        error = "No search engines configured"
    elif not all_results:
        error = "All search engines returned no results"

    return {"results": all_results, "error": error}
