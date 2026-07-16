from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from ..models import KnowledgeNode, Poster
from ..services.ai_service import search_external
from ..services.embeddings_service import get_embedding, search_posters_by_vector
from ..utils.search_logger import log_search
import time

search_bp = Blueprint("search", __name__)

_EMBEDDING_ENABLED = False  # flipped by _check_embedding() at runtime

_SORT_OPTIONS = {
    "relevance": None,  # handled specially
    "created_at": Poster.created_at,
    "title": Poster.title,
    "event_time": Poster.event_time,
}


def _external_result_item(result: dict, index: int) -> dict:
    return {
        "hit_type": "external",
        "item": {
            "id": -index,
            "title": result.get("title") or "外部搜索结果",
            "raw_text": result.get("summary") or "",
            "summary": result.get("summary") or "",
            "event_time": None,
            "location": None,
            "organizer": result.get("source"),
            "status": "published",
            "activity_type": "外部",
            "created_at": None,
            "source_url": result.get("url"),
        },
        "source": result.get("source"),
        "url": result.get("url"),
    }


def _check_embedding():
    """Check whether embedding/vector search is available at runtime."""
    global _EMBEDDING_ENABLED
    try:
        _EMBEDDING_ENABLED = bool(current_app.config.get("EMBEDDING_ENABLED", False))
    except RuntimeError:
        _EMBEDDING_ENABLED = False


def _parse_sort_params() -> tuple[str, str]:
    """Parse and validate sort / order query parameters."""
    sort = (request.args.get("sort") or "relevance").strip().lower()
    if sort not in _SORT_OPTIONS:
        sort = "relevance"
    order = (request.args.get("order") or "desc").strip().lower()
    if order not in ("asc", "desc"):
        order = "desc"
    return sort, order


@search_bp.get("/internal")
@jwt_required()
def internal_search():
    t0 = time.time()
    keyword = (request.args.get("q") or "").strip()
    if not keyword:
        log_search("internal", keyword, 0, 0, {}, "none")
        return jsonify({"items": [], "query": keyword})

    sort, order = _parse_sort_params()
    _check_embedding()

    use_vector = _EMBEDDING_ENABLED and sort == "relevance"

    # Vector (semantic) search — only active when EMBEDDING_ENABLED=true
    if use_vector:
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
        query = Poster.query.filter(
            or_(
                Poster.title.like(like_value),
                Poster.summary.like(like_value),
                Poster.raw_text.like(like_value),
                Poster.location.like(like_value),
                Poster.organizer.like(like_value),
            )
        )

        # Apply sort
        sort_col = _SORT_OPTIONS.get(sort)
        if sort_col is not None:
            order_fn = sort_col.desc if order == "desc" else sort_col.asc
            query = query.order_by(order_fn(), Poster.id.desc())
        else:
            query = query.order_by(Poster.created_at.desc())

        posters = query.limit(20).all()

    # Knowledge nodes — always use LIKE, unaffected by sort
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

    latency_ms = (time.time() - t0) * 1000

    result_types = {"poster": len(posters), "knowledge_node": len(nodes)}
    log_search(
        endpoint="internal",
        query=keyword,
        latency_ms=latency_ms,
        hit_count=len(items),
        result_types=result_types,
        search_mode="vector" if use_vector else "fulltext",
        sort=sort,
        order=order,
    )
    return jsonify({
        "items": items,
        "query": keyword,
        "search_mode": "vector" if use_vector else "fulltext",
        "sort": sort,
        "order": order,
    })


# ---------------------------------------------------------------------------
# External search (doc-aligned GET route)
# ---------------------------------------------------------------------------


@search_bp.get("/external")
@jwt_required()
def external_search():
    """Search external sources using real search engines (SearXNG + Sogou).

    Engines used by default: Google, Bing, DuckDuckGo, Baidu, Sogou.
    Falls back to LLM knowledge when no search results found.

    Aligns with the documented ``GET /api/search/external?q=...`` interface.
    For advanced parameters (sources, etc.), use ``POST /api/ai/search``.
    Pass ?sources=web,sogou,llm to specify which sources to query.
    """
    t0 = time.time()
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "query parameter 'q' is required"}), 400

    # Parse optional source filter from query string
    sources_raw = request.args.get("sources")
    sources = [s.strip() for s in sources_raw.split(",")] if sources_raw else None

    result = search_external(query, sources=sources)

    latency_ms = (time.time() - t0) * 1000

    source_counts: dict[str, int] = {}
    for r in result["results"]:
        src = r.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    log_search(
        endpoint="external",
        query=query,
        latency_ms=latency_ms,
        hit_count=len(result["results"]),
        result_types=source_counts,
        search_mode="multi",
        error=result.get("error"),
    )
    items = [
        _external_result_item(item, index + 1)
        for index, item in enumerate(result["results"])
    ]

    return jsonify({
        "query": query,
        "results": result["results"],
        "count": len(result["results"]),
        "items": items,
        "page": 1,
        "per_page": len(items) or 10,
        "total": len(items),
        "search_mode": "external",
        "source": "multi",
        "error": result.get("error"),
    })


@search_bp.post("/search/poster-preview")
@jwt_required()
def poster_preview():
    """Generate a poster HTML from external search result title+summary."""
    from flask import Response

    from ..services.poster_service import generate_poster_html

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    summary = (payload.get("summary") or "").strip()
    source = (payload.get("source") or "").strip()

    if not title:
        return jsonify({"message": "title is required"}), 400

    html = generate_poster_html(
        title=title,
        summary=summary,
        organizer=source or None,
        activity_type="外部",
    )
    return Response(html, mimetype="text/html")
