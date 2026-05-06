from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from ..models import KnowledgeNode


knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.get("/nodes")
@jwt_required()
def list_nodes():
    keyword = (request.args.get("q") or "").strip()
    node_type = (request.args.get("node_type") or "").strip()

    query = KnowledgeNode.query.order_by(KnowledgeNode.node_type.asc(), KnowledgeNode.name.asc())
    if node_type:
        query = query.filter_by(node_type=node_type)
    if keyword:
        like_value = f"%{keyword}%"
        query = query.filter(
            or_(
                KnowledgeNode.name.like(like_value),
                KnowledgeNode.description.like(like_value),
            )
        )

    return jsonify({"items": [node.to_dict() for node in query.all()]})


@knowledge_bp.get("/nodes/<int:node_id>")
@jwt_required()
def get_node(node_id: int):
    node = KnowledgeNode.query.get_or_404(node_id)
    posters = [
        {
            "relation_type": poster_node.relation_type,
            "matched_by": poster_node.matched_by,
            "poster": poster_node.poster.to_dict(),
        }
        for poster_node in node.posters
    ]
    payload = node.to_dict()
    payload["posters"] = posters
    return jsonify({"item": payload})
