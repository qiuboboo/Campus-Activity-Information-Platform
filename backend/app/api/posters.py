from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Poster
from ..services.knowledge_service import rebuild_poster_knowledge, related_payload
from ..services.poster_service import build_poster_fields
from ..utils.auth import roles_required


posters_bp = Blueprint("posters", __name__)


@posters_bp.get("")
@jwt_required()
def list_posters():
    keyword = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(
        min(int(request.args.get("per_page", current_app.config["POSTERS_PER_PAGE"])), 50),
        1,
    )

    query = Poster.query.order_by(Poster.created_at.desc())
    if keyword:
        like_value = f"%{keyword}%"
        query = query.filter(
            or_(
                Poster.title.like(like_value),
                Poster.summary.like(like_value),
                Poster.raw_text.like(like_value),
            )
        )
    if status:
        query = query.filter_by(status=status)

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [poster.to_dict() for poster in items.items],
            "page": page,
            "per_page": per_page,
            "total": items.total,
        }
    )


@posters_bp.post("")
@roles_required("publisher", "admin")
def create_poster():
    payload = request.get_json(silent=True) or {}
    raw_text = (payload.get("raw_text") or "").strip()
    if not raw_text:
        return jsonify({"message": "raw_text is required"}), 400

    parsed = build_poster_fields(payload)
    poster = Poster(created_by=int(get_jwt_identity()), **parsed)
    db.session.add(poster)
    db.session.flush()
    if poster.status == "published":
        rebuild_poster_knowledge(poster)
    db.session.commit()
    return jsonify({"item": poster.to_dict()}), 201


@posters_bp.get("/<int:poster_id>")
@jwt_required()
def get_poster(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)
    return jsonify({"item": poster.to_dict()})


@posters_bp.get("/<int:poster_id>/related")
@jwt_required()
def get_related(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)
    return jsonify(related_payload(poster))


@posters_bp.put("/<int:poster_id>")
@roles_required("publisher", "admin")
def update_poster(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)
    payload = request.get_json(silent=True) or {}

    if payload.get("raw_text") is not None and not str(payload.get("raw_text")).strip():
        return jsonify({"message": "raw_text cannot be empty"}), 400

    parsed = build_poster_fields(payload, fallback=poster)
    for key, value in parsed.items():
        setattr(poster, key, value)

    if poster.status == "published":
        rebuild_poster_knowledge(poster)
    db.session.commit()
    return jsonify({"item": poster.to_dict()})


@posters_bp.post("/<int:poster_id>/review")
@roles_required("admin")
def review_poster(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)
    payload = request.get_json(silent=True) or {}
    action = (payload.get("action") or "").strip().lower()
    comment = (payload.get("comment") or "").strip()

    if action not in {"approve", "reject"}:
        return jsonify({"message": "action must be approve or reject"}), 400

    poster.status = "published" if action == "approve" else "rejected"
    poster.review_comment = comment or None
    if poster.status == "published":
        rebuild_poster_knowledge(poster)
    db.session.commit()

    return jsonify({"item": poster.to_dict()})
