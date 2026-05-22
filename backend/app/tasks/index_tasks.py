"""Celery tasks for embedding/index operations (queue: index).

Requires ``EMBEDDING_ENABLED=true`` and a configured embedding API.
Tasks are no-ops when embedding is disabled.
"""

from __future__ import annotations

import json
import logging

from ..celery_app import celery
from ..config import Config

logger = logging.getLogger(__name__)


def _embedding_enabled() -> bool:
    from flask import current_app

    return current_app.config.get("EMBEDDING_ENABLED", False)


@celery.task(bind=True, max_retries=2, soft_time_limit=60, queue="index")
def build_poster_embedding(self, poster_id: int) -> dict:
    """Generate and store vector embedding for a poster."""
    from .. import create_app

    app = create_app(Config)
    with app.app_context():
        if not _embedding_enabled():
            return {"success": False, "info": "embedding disabled (EMBEDDING_ENABLED=false)"}

        try:
            from ..extensions import db
            from ..models import Poster
            from ..services.embeddings_service import get_embedding

            poster = db.session.get(Poster, poster_id)
            if poster is None:
                return {"success": False, "error": f"Poster {poster_id} not found"}

            embed_text = f"{poster.title} {poster.summary} {poster.raw_text[:2000]}"
            vector = get_embedding(embed_text)
            if vector is None:
                return {"success": False, "error": "embedding API returned None"}

            poster.embedding = json.dumps(vector)
            db.session.commit()

            logger.info(
                "build_poster_embedding(%d): dim=%d, text_len=%d",
                poster_id,
                len(vector),
                len(embed_text),
            )
            return {
                "success": True,
                "poster_id": poster_id,
                "dimensions": len(vector),
                "text_length": len(embed_text),
            }
        except Exception as e:
            logger.exception("build_poster_embedding failed for poster %d", poster_id)
            return {"success": False, "error": str(e)}


@celery.task(bind=True, max_retries=2, soft_time_limit=60, queue="index")
def build_node_embedding(self, node_id: int) -> dict:
    """Generate and store vector embedding for a knowledge node."""
    from .. import create_app

    app = create_app(Config)
    with app.app_context():
        if not _embedding_enabled():
            return {"success": False, "info": "embedding disabled (EMBEDDING_ENABLED=false)"}

        try:
            from ..extensions import db
            from ..models import KnowledgeNode
            from ..services.embeddings_service import get_embedding

            node = db.session.get(KnowledgeNode, node_id)
            if node is None:
                return {"success": False, "error": f"Node {node_id} not found"}

            embed_text = f"{node.name} {node.description or ''}"
            vector = get_embedding(embed_text)
            if vector is None:
                return {"success": False, "error": "embedding API returned None"}

            node.embedding = json.dumps(vector)
            db.session.commit()

            logger.info(
                "build_node_embedding(%d): dim=%d, text_len=%d",
                node_id,
                len(vector),
                len(embed_text),
            )
            return {
                "success": True,
                "node_id": node_id,
                "dimensions": len(vector),
                "text_length": len(embed_text),
            }
        except Exception as e:
            logger.exception("build_node_embedding failed for node %d", node_id)
            return {"success": False, "error": str(e)}


@celery.task(bind=True, soft_time_limit=300, queue="index")
def rebuild_all_embeddings(self) -> dict:
    """Rebuild embeddings for all posters and knowledge nodes."""
    from .. import create_app

    app = create_app(Config)
    with app.app_context():
        if not _embedding_enabled():
            return {"success": False, "info": "embedding disabled (EMBEDDING_ENABLED=false)"}

        from ..extensions import db
        from ..models import KnowledgeNode, Poster
        from ..services.embeddings_service import get_embedding

        posters = Poster.query.all()
        poster_ok = 0
        for p in posters:
            embed_text = f"{p.title} {p.summary} {p.raw_text[:2000]}"
            vector = get_embedding(embed_text)
            if vector:
                p.embedding = json.dumps(vector)
                poster_ok += 1
        db.session.commit()

        nodes = KnowledgeNode.query.all()
        node_ok = 0
        for n in nodes:
            embed_text = f"{n.name} {n.description or ''}"
            vector = get_embedding(embed_text)
            if vector:
                n.embedding = json.dumps(vector)
                node_ok += 1
        db.session.commit()

        logger.info(
            "rebuild_all_embeddings: %d/%d posters, %d/%d nodes",
            poster_ok,
            len(posters),
            node_ok,
            len(nodes),
        )
        return {
            "success": True,
            "posters_total": len(posters),
            "posters_ok": poster_ok,
            "nodes_total": len(nodes),
            "nodes_ok": node_ok,
        }
