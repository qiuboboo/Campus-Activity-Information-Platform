"""Celery tasks for embedding/index operations (queue: index).

Requires ``EMBEDDING_ENABLED=true`` and pgvector extension on PostgreSQL.
Tasks are no-ops when embedding is disabled.
"""

from __future__ import annotations

import logging

from ..celery_app import celery
from ..config import Config

logger = logging.getLogger(__name__)


def _embedding_enabled() -> bool:
    """Check if embedding/index features are configured."""
    from flask import current_app

    return current_app.config.get("EMBEDDING_ENABLED", False)


@celery.task(bind=True, max_retries=2, soft_time_limit=60, queue="index")
def build_poster_embedding(self, poster_id: int) -> dict:
    """Generate and store vector embedding for a poster.

    Requires ``EMBEDDING_ENABLED=true``.  No-op when disabled.
    """
    from .. import create_app

    app = create_app(Config)
    with app.app_context():
        if not _embedding_enabled():
            return {"success": False, "info": "embedding disabled (EMBEDDING_ENABLED=false)"}

        try:
            from ..extensions import db
            from ..models import Poster

            poster = db.session.get(Poster, poster_id)
            if poster is None:
                return {"success": False, "error": f"Poster {poster_id} not found"}

            # Build embedding text from poster fields
            embed_text = f"{poster.title} {poster.summary} {poster.raw_text[:2000]}"

            # TODO: call embedding API and store on poster.embedding
            # placeholder — embedding API integration pending
            logger.info("build_poster_embedding(%d): text length=%d", poster_id, len(embed_text))

            return {"success": True, "poster_id": poster_id, "text_length": len(embed_text)}
        except Exception as e:
            logger.exception("build_poster_embedding failed for poster %d", poster_id)
            return {"success": False, "error": str(e)}


@celery.task(bind=True, max_retries=2, soft_time_limit=60, queue="index")
def build_node_embedding(self, node_id: int) -> dict:
    """Generate and store vector embedding for a knowledge node.

    Requires ``EMBEDDING_ENABLED=true``.  No-op when disabled.
    """
    from .. import create_app

    app = create_app(Config)
    with app.app_context():
        if not _embedding_enabled():
            return {"success": False, "info": "embedding disabled (EMBEDDING_ENABLED=false)"}

        try:
            from ..extensions import db
            from ..models import KnowledgeNode

            node = db.session.get(KnowledgeNode, node_id)
            if node is None:
                return {"success": False, "error": f"Node {node_id} not found"}

            embed_text = f"{node.name} {node.description or ''}"

            # TODO: call embedding API and store on node.embedding
            # placeholder — embedding API integration pending
            logger.info("build_node_embedding(%d): text length=%d", node_id, len(embed_text))

            return {"success": True, "node_id": node_id, "text_length": len(embed_text)}
        except Exception as e:
            logger.exception("build_node_embedding failed for node %d", node_id)
            return {"success": False, "error": str(e)}
