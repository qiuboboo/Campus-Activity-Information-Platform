"""Text embedding service backed by an OpenAI-compatible API.

Uses the configured ``EMBEDDING_API_URL`` (defaults to the Copilot Pro proxy
at ``http://copilot-proxy:4141/v1/embeddings``) and ``EMBEDDING_MODEL``
(default ``text-embedding-3-small``, 1536 dimensions).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from ..config import Config

logger = logging.getLogger(__name__)

_EMBEDDING_CACHE: dict[str, list[float]] = {}


def _api_config() -> dict[str, Any]:
    return {
        "url": Config.EMBEDDING_API_URL,
        "key": Config.EMBEDDING_API_KEY,
        "model": Config.EMBEDDING_MODEL,
    }


def get_embedding(text: str, use_cache: bool = True) -> list[float] | None:
    """Convert *text* to a vector embedding.

    Returns a 1536-dimensional float list, or ``None`` on failure.
    """
    key = text.strip()
    if not key:
        return None

    if use_cache and key in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[key]

    cfg = _api_config()
    try:
        resp = requests.post(
            cfg["url"],
            json={"model": cfg["model"], "input": [key]},
            headers={"Authorization": f"Bearer {cfg['key']}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        vector: list[float] = data["data"][0]["embedding"]
    except Exception:
        logger.exception("embedding API call failed for text (len=%d)", len(key))
        return None

    _EMBEDDING_CACHE[key] = vector
    return vector


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(av * bv for av, bv in zip(a, b))
    na = sum(av * av for av in a) ** 0.5
    nb = sum(bv * bv for bv in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search_posters_by_vector(
    query_embedding: list[float],
    posters: list[Any],
    *,
    limit: int = 20,
    min_score: float = 0.0,
) -> list[tuple[float, Any]]:
    """Rank *posters* by cosine similarity to *query_embedding*.

    Returns ``[(score, poster), ...]`` sorted descending, filtered to
    ``score >= min_score`` and capped at *limit*.
    """
    scored: list[tuple[float, Any]] = []
    for p in posters:
        if not p.embedding:
            continue
        try:
            emb = json.loads(p.embedding)
        except (json.JSONDecodeError, TypeError):
            continue
        score = cosine_similarity(query_embedding, emb)
        if score >= min_score:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]
