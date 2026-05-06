from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from ..models import KnowledgeNode, Poster


search_bp = Blueprint("search", __name__)


@search_bp.get("/internal")
@jwt_required()
def internal_search():
    keyword = (request.args.get("q") or "").strip()
    if not keyword:
        return jsonify({"items": [], "query": keyword})

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
    return jsonify({"items": items, "query": keyword})
