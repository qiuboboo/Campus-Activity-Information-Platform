from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
from ..models import KnowledgeNode, Poster, PosterLink, PosterNode
from ..services.audit_service import create_audit_log
from ..services.knowledge_service import rebuild_poster_knowledge
from ..utils.auth import roles_required


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


@knowledge_bp.post("/rebuild")
@roles_required("admin")
def rebuild_all_knowledge():
    payload = request.get_json(silent=True) or {}
    status_filter = (payload.get("status") or "").strip() or "published"
    source_type = (payload.get("source_type") or "").strip()

    query = Poster.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if source_type:
        query = query.filter_by(source_type=source_type)

    posters = query.all()
    total = len(posters)
    succeeded = 0
    failed = 0
    errors = []

    for poster in posters:
        try:
            PosterNode.query.filter_by(poster_id=poster.id).delete()
            PosterLink.query.filter_by(from_poster_id=poster.id).delete()
            rebuild_poster_knowledge(poster)
            db.session.flush()
            succeeded += 1
        except Exception as e:
            db.session.rollback()
            failed += 1
            errors.append({"id": poster.id, "error": str(e)})

    if succeeded > 0:
        db.session.commit()

    # Also rebuild embeddings when enabled
    rebuild_embeddings = payload.get("rebuild_embeddings", False)
    emb_result = None
    if rebuild_embeddings and current_app.config.get("EMBEDDING_ENABLED"):
        from ..tasks.index_tasks import rebuild_all_embeddings

        emb_result = rebuild_all_embeddings.delay()
        emb_result = {"task_id": emb_result.id}

    actor_id = int(get_jwt_identity())
    create_audit_log(
        actor_id=actor_id,
        action="rebuild_all_knowledge",
        target_type="knowledge",
        summary=f"Rebuilt knowledge for {succeeded}/{total} posters (failed: {failed})",
        metadata={"total": total, "succeeded": succeeded, "failed": failed, "errors": errors[:10]},
    )
    db.session.commit()

    return jsonify({
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "errors": errors[:10],
        "embeddings": emb_result,
    })
