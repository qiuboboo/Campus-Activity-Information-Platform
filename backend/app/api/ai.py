"""Unified AI API blueprint.

Provides a single entry point for all AI-related operations:
extraction, enrichment, search, and MCP tool access.
"""

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from ..utils.auth import roles_required

ai_bp = Blueprint("ai", __name__)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


@ai_bp.get("/ai/status")
@jwt_required()
def status():
    """Check whether AI services are configured and reachable."""
    llm_key = bool(current_app.config.get("LLM_API_KEY", ""))
    mcp_servers = current_app.config.get("MCP_SERVERS", "")

    from ..services.mcp_service import list_servers
    server_status = list_servers()

    return jsonify({
        "llm_configured": llm_key,
        "mcp_servers": server_status,
    })


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


@ai_bp.post("/ai/extract")
@jwt_required()
def extract():
    """Extract structured activity fields from raw text.

    Request body::

        {"text": "活动原文...", "source": "optional-source-label"}

    Returns extracted fields: title, event_time, location, organizer, tags, etc.
    """
    data = request.get_json(force=True)
    raw_text = (data.get("text") or "").strip()
    if not raw_text:
        return jsonify({"error": "text is required"}), 400

    from ..services.ai_service import extract_from_text
    result = extract_from_text(raw_text)

    if not result:
        return jsonify({"error": "Extraction failed (LLM unavailable)", "fields": {}}), 503

    # Convert datetime objects to ISO strings for JSON serialisation
    for field in ("event_time",):
        if isinstance(result.get(field), object) and hasattr(result.get(field), "isoformat"):
            result[field] = result[field].isoformat()

    return jsonify({"fields": result})


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


@ai_bp.post("/ai/enrich/<int:poster_id>")
@roles_required("admin")
def enrich(poster_id: int):
    """Enrich a poster with AI-generated summary, tags, and keywords."""
    from ..services.ai_service import enrich_poster
    result = enrich_poster(poster_id)

    if not result:
        return jsonify({"error": "Enrichment failed (LLM unavailable or poster not found)"}), 503

    from ..extensions import db
    from ..models import Poster
    poster = db.session.get(Poster, poster_id)
    return jsonify({"item": poster.to_dict() if poster else None, "ai_result": result})


# ---------------------------------------------------------------------------
# External search (LLM-based)
# ---------------------------------------------------------------------------


@ai_bp.post("/ai/search")
@jwt_required()
def search():
    """Search for activity information using LLM knowledge.

    Request body::

        {"query": "中山大学 2025 科技节", "sources": ["校园网站", "小红书"]}
    """
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    from ..services.ai_service import search_external
    results = search_external(query, sources=data.get("sources"))

    return jsonify({"query": query, "results": results, "count": len(results)})


# ---------------------------------------------------------------------------
# MCP server management
# ---------------------------------------------------------------------------


@ai_bp.get("/ai/mcp/servers")
@jwt_required()
def list_mcp_servers():
    """List configured MCP servers and their running status."""
    from ..services.mcp_service import list_servers
    return jsonify({"servers": list_servers()})


@ai_bp.post("/ai/mcp/call")
@roles_required("admin")
def call_mcp_tool():
    """Call a tool on an MCP server.

    Request body::

        {"server": "xiaohongshu", "tool": "search_notes", "params": {"query": "校园活动"}}
    """
    data = request.get_json(force=True)
    server = (data.get("server") or "").strip()
    tool = (data.get("tool") or "").strip()
    params = data.get("params") or {}

    if not server:
        return jsonify({"error": "server is required"}), 400
    if not tool:
        return jsonify({"error": "tool is required"}), 400

    from ..services.mcp_service import call_tool
    result = call_tool(server, tool, params)

    if result is None:
        return jsonify({"error": f"MCP call failed (server '{server}' unavailable or not configured)"}), 503

    return jsonify({"server": server, "tool": tool, "result": result})
