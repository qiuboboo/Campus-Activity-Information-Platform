"""Lightweight structured search logging — emits one JSON line per search call.

Design:
- Zero extra dependencies (uses only stdlib ``logging`` + ``json``)
- Query is masked before logging (Chinese chars: keep first/last; ASCII: same)
- Output is valid JSON lines, parsable by ``jq`` / log aggregators
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger("search")

# ---------------------------------------------------------------------------
# Query masking
# ---------------------------------------------------------------------------


def mask_query(q: str) -> str:
    """Return a privacy-safe version of *q*.

    Rules:
    - Empty string → ``""``
    - Chinese characters: keep first and last, middle replaced with ``***``
    - Non-CJK strings ≤ 3 chars: return as-is
    - Non-CJK strings > 3 chars: keep first char + ``***`` + last char
    """
    if not q:
        return ""

    cjk = re.findall(r"[一-鿿]", q)
    if cjk:
        # Mask middle CJK characters
        if len(cjk) <= 2:
            return q
        return q[0] + "***" + q[-1] if len(q) > 1 else q

    # Non-CJK
    if len(q) <= 3:
        return q
    return q[0] + "***" + q[-1]


# ---------------------------------------------------------------------------
# Structured log emitter
# ---------------------------------------------------------------------------

_SEARCH_FIELDS = [
    "endpoint",
    "query_masked",
    "latency_ms",
    "hit_count",
    "result_types",
    "search_mode",
    "sort",
    "order",
    "error",
    "request_id",
    "user_id",
    "timestamp",
]


def _get_request_id() -> str:
    """Extract request_id from Flask request context, or ``"unknown"``."""
    try:
        from flask import request

        return getattr(request, "request_id", "unknown")
    except RuntimeError:
        return "unknown"


def _get_user_id() -> str | None:
    """Extract current user ID from Flask-JWT current_user, or ``None``."""
    try:
        from flask_jwt_extended import get_current_user

        user = get_current_user()
        if user is not None:
            return getattr(user, "id", None)
    except Exception:
        pass
    return None


def log_search(
    endpoint: str,
    query: str,
    latency_ms: float,
    hit_count: int,
    result_types: dict[str, int],
    search_mode: str,
    sort: str | None = None,
    order: str | None = None,
    error: str | None = None,
) -> None:
    """Emit one structured JSON log line for a completed search."""
    entry = {
        "endpoint": endpoint,
        "query_masked": mask_query(query),
        "latency_ms": round(latency_ms, 2),
        "hit_count": hit_count,
        "result_types": result_types,
        "search_mode": search_mode,
        "sort": sort,
        "order": order,
        "error": error,
        "request_id": _get_request_id(),
        "user_id": _get_user_id(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{time.time() % 1:.6f}"[2:8] + "Z",
    }
    logger.info(json.dumps(entry, ensure_ascii=False, default=str))
