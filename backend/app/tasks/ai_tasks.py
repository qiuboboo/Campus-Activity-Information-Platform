"""Celery tasks for AI operations (queue: ai).

Includes LLM extraction, enrichment, and search as async tasks
so the API layer can submit them and return immediately.
"""

from __future__ import annotations

import logging

from ..celery_app import celery
from ..config import Config

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=2, soft_time_limit=120, queue="ai")
def ai_extract_task(self, raw_text: str, profile: str | None = None) -> dict:
    """Async: extract structured activity fields from *raw_text*.

    Stores the result in the Celery result backend for later retrieval.
    """
    from .. import create_app
    from ..services.ai_service import extract_from_text

    app = create_app(Config)
    with app.app_context():
        try:
            result = extract_from_text(raw_text, profile=profile)
            return {"success": True, "fields": result}
        except Exception as e:
            logger.exception("ai_extract_task failed")
            return {"success": False, "error": str(e)}


@celery.task(bind=True, max_retries=2, soft_time_limit=120, queue="ai")
def ai_enrich_task(self, poster_id: int) -> dict:
    """Async: enrich a poster with AI-generated summary and tags."""
    from .. import create_app
    from ..services.ai_service import enrich_poster

    app = create_app(Config)
    with app.app_context():
        try:
            result = enrich_poster(poster_id)
            if result:
                return {"success": True, "poster_id": poster_id, "result": result}
            return {"success": False, "error": "Enrichment returned empty"}
        except Exception as e:
            logger.exception("ai_enrich_task failed for poster %d", poster_id)
            return {"success": False, "error": str(e)}
