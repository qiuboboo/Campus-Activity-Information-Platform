from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from ..models import KnowledgeNode, Poster


search_bp = Blueprint("search", __name__)

_EMBEDDING_ENABLED = False  # flipped by _check_embedding() at runtime


def _check_embedding():
    """Check whether embedding/vector search is available at runtime."""
    global _EMBEDDING_ENABLED
    try:
        _EMBEDDING_ENABLED = bool(current_app.config.get("EMBEDDING_ENABLED", False))
    except RuntimeError:
        _EMBEDDING_ENABLED = False


@search_bp.get("/internal")
@jwt_required()
def internal_search():
    keyword = (request.args.get("q") or "").strip()
    if not keyword:
        return jsonify({"items": [], "query": keyword})

    _check_embedding()

    # Vector (semantic) search — only active when EMBEDDING_ENABLED=true
    if _EMBEDDING_ENABLED:
        from ..services.embeddings_service import get_embedding, search_posters_by_vector

        query_emb = get_embedding(keyword)
        if query_emb:
            posters_with_emb = Poster.query.filter(Poster.embedding.isnot(None)).all()
            scored = search_posters_by_vector(query_emb, posters_with_emb, limit=20, min_score=0.0)
            poster_ids = {p.id for _, p in scored}

            # Add any LIKE matches not found by vector search
            like_value = f"%{keyword}%"
            extra = (
                Poster.query.filter(
                    or_(
                        Poster.title.like(like_value),
                        Poster.summary.like(like_value),
                        Poster.raw_text.like(like_value),
                        Poster.location.like(like_value),
                        Poster.organizer.like(like_value),
                    )
                )
                .filter(~Poster.id.in_(poster_ids))
                .order_by(Poster.created_at.desc())
                .limit(20)
                .all()
            )

            posters = [p for _, p in scored] + extra
        else:
            posters = []
    else:
        # Full-text (LIKE) search — always available
        like_value = f"%{keyword}%"
        posters = (
            Poster.query.filter(
                or_(
                    Poster.title.like(like_value),
                    Poster.summary.like(like_value),
                    Poster.raw_text.like(like_value),
                    Poster.location.like(like_value),
                    Poster.organizer.like(like_value),
                )
            )
            .order_by(Poster.created_at.desc())
            .limit(20)
            .all()
        )

    # Knowledge nodes — always use LIKE
    like_value = f"%{keyword}%"
    nodes = (
        KnowledgeNode.query.filter(
            or_(
                KnowledgeNode.name.like(like_value),
                KnowledgeNode.description.like(like_value),
            )
        )
        .order_by(KnowledgeNode.node_type.asc(), KnowledgeNode.name.asc())
        .limit(20)
        .all()
    )

    items = [{"hit_type": "poster", "item": poster.to_dict()} for poster in posters]
    items.extend({"hit_type": "knowledge_node", "item": node.to_dict()} for node in nodes)
    return jsonify({
        "items": items,
        "query": keyword,
        "search_mode": "vector" if _EMBEDDING_ENABLED else "fulltext",
    })


# ---------------------------------------------------------------------------
# External search (doc-aligned GET route)
# ---------------------------------------------------------------------------


@search_bp.get("/external")
@jwt_required()
def external_search():
    """Search external sources using LLM knowledge.

    Aligns with the documented ``GET /api/search/external?q=...`` interface.
    For advanced parameters (sources, etc.), use ``POST /api/ai/search``.
    """
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "query parameter 'q' is required"}), 400

    from ..services.ai_service import search_external

    result = search_external(query)
    return jsonify({
        "query": query,
        "results": result["results"],
        "count": len(result["results"]),
        "source": "llm",
        "error": result.get("error"),
    })
