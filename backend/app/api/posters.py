from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Poster, PosterNode, PosterLink
from ..services.audit_service import create_audit_log
from ..services.knowledge_service import rebuild_poster_knowledge, related_payload
from ..services.notification_service import dispatch_notifications
from ..services.poster_service import build_poster_fields, generate_poster_html
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
    poster.content_html = generate_poster_html(
        title=poster.title,
        summary=poster.summary,
        event_time=poster.event_time,
        location=poster.location,
        organizer=poster.organizer,
        activity_type=poster.activity_type,
    )
    db.session.add(poster)
    db.session.flush()
    if poster.status == "published":
        rebuild_poster_knowledge(poster)
        dispatch_notifications(poster)
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

    # Regenerate HTML when relevant content changes
    if any(k in payload for k in ("title", "summary", "event_time", "location", "organizer")):
        poster.content_html = generate_poster_html(
            title=poster.title,
            summary=poster.summary,
            event_time=poster.event_time,
            location=poster.location,
            organizer=poster.organizer,
            activity_type=poster.activity_type,
        )

    if poster.status == "published":
        rebuild_poster_knowledge(poster)
        dispatch_notifications(poster)
    db.session.commit()
    return jsonify({"item": poster.to_dict()})


@posters_bp.post("/<int:poster_id>/submit")
@roles_required("publisher", "admin")
def submit_poster(poster_id: int):
    """Submit a draft poster for review (draft → pending_review)."""
    poster = Poster.query.get_or_404(poster_id)
    if poster.status != "draft":
        return jsonify({"message": f"cannot submit poster with status '{poster.status}'"}), 400

    poster.status = "pending_review"
    create_audit_log(
        actor_id=int(get_jwt_identity()),
        action="submit",
        target_type="poster",
        target_id=poster.id,
        summary=f"Submitted poster '{poster.title}' for review",
    )
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
    if poster.status not in {"pending_review", "draft"}:
        return jsonify({"message": f"cannot review poster with status '{poster.status}'"}), 400

    old_status = poster.status
    poster.status = "published" if action == "approve" else "rejected"
    poster.review_comment = comment or None
    if poster.status == "published":
        rebuild_poster_knowledge(poster)
        dispatch_notifications(poster)
    db.session.flush()

    actor_id = int(get_jwt_identity())
    create_audit_log(
        actor_id=actor_id,
        action=f"review_{action}",
        target_type="poster",
        target_id=poster.id,
        summary=f"Review {action}: poster '{poster.title}' (status: {old_status} -> {poster.status})",
        metadata={"review_comment": comment} if comment else None,
    )
    db.session.commit()

    return jsonify({"item": poster.to_dict()})


@posters_bp.get("/review-queue")
@roles_required("admin")
def review_queue():
    status_filter = (request.args.get("status") or "").strip()
    source_type = (request.args.get("source_type") or "").strip()
    duplicate_group_key = (request.args.get("duplicate_group_key") or "").strip()
    sort_by = (request.args.get("sort_by") or "-created_at").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)

    query = Poster.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    else:
        query = query.filter(Poster.status.in_(["pending_review", "draft", "rejected"]))

    if source_type:
        query = query.filter_by(source_type=source_type)
    if duplicate_group_key:
        query = query.filter_by(duplicate_group_key=duplicate_group_key)

    # Sorting
    if sort_by.startswith("-"):
        sort_col = getattr(Poster, sort_by[1:], None)
        if sort_col is not None:
            query = query.order_by(sort_col.desc())
    else:
        sort_col = getattr(Poster, sort_by, None)
        if sort_col is not None:
            query = query.order_by(sort_col)

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [poster.to_dict() for poster in items.items],
        "page": page,
        "per_page": per_page,
        "total": items.total,
    })


@posters_bp.post("/bulk-review")
@roles_required("admin")
def bulk_review():
    payload = request.get_json(silent=True) or {}
    poster_ids = payload.get("poster_ids", [])
    action = (payload.get("action") or "").strip().lower()
    comment = (payload.get("comment") or "").strip()

    if not poster_ids:
        return jsonify({"error": "poster_ids is required"}), 400
    if action not in {"approve", "reject"}:
        return jsonify({"message": "action must be approve or reject"}), 400

    actor_id = int(get_jwt_identity())
    succeeded = []
    failed = []

    for pid in poster_ids:
        poster = Poster.query.get(pid)
        if poster is None:
            failed.append({"id": pid, "error": "not found"})
            continue

        old_status = poster.status
        poster.status = "published" if action == "approve" else "rejected"
        poster.review_comment = comment or None
        if poster.status == "published":
            try:
                rebuild_poster_knowledge(poster)
                dispatch_notifications(poster)
            except Exception:
                failed.append({"id": pid, "error": "knowledge rebuild failed"})
                continue
        db.session.flush()

        create_audit_log(
            actor_id=actor_id,
            action=f"bulk_review_{action}",
            target_type="poster",
            target_id=poster.id,
            summary=f"Bulk review {action}: poster '{poster.title}' (status: {old_status} -> {poster.status})",
            metadata={"review_comment": comment} if comment else None,
        )
        succeeded.append({"id": pid, "status": poster.status})

    db.session.commit()
    return jsonify({"succeeded": succeeded, "failed": failed})


@posters_bp.get("/<int:poster_id>/duplicates")
@roles_required("admin")
def get_duplicates(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)
    seen = set()
    candidates = []

    # Same duplicate_group_key
    if poster.duplicate_group_key:
        group_members = Poster.query.filter(
            Poster.duplicate_group_key == poster.duplicate_group_key,
            Poster.id != poster.id,
        ).all()
        for p in group_members:
            seen.add(p.id)
            candidates.append(p)

    # Same source_fingerprint
    if poster.source_fingerprint:
        fingerprint_members = Poster.query.filter(
            Poster.source_fingerprint == poster.source_fingerprint,
            Poster.id != poster.id,
        ).all()
        for p in fingerprint_members:
            if p.id not in seen:
                seen.add(p.id)
                candidates.append(p)

    return jsonify({
        "poster": poster.to_dict(),
        "duplicates": [p.to_dict() for p in candidates],
        "count": len(candidates),
    })


@posters_bp.post("/<int:poster_id>/merge-source")
@roles_required("admin")
def merge_source(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)
    payload = request.get_json(silent=True) or {}
    source_poster_id = payload.get("source_poster_id")

    if not source_poster_id:
        return jsonify({"error": "source_poster_id is required"}), 400

    source = Poster.query.get(source_poster_id)
    if source is None:
        return jsonify({"error": "Source poster not found"}), 404

    actor_id = int(get_jwt_identity())
    merged_urls = []

    # Absorb source URLs into main poster
    if source.source_url and source.source_url != poster.source_url:
        merged_urls.append(source.source_url)

    # Record merged source_urls in metadata
    metadata = {
        "merged_from_poster_id": source.id,
        "merged_from_title": source.title,
        "merged_urls": merged_urls,
    }

    # Delete source poster (cascade will remove its nodes/links)
    db.session.delete(source)
    db.session.flush()

    # Rebuild knowledge for the main poster
    rebuild_poster_knowledge(poster)
    db.session.flush()

    create_audit_log(
        actor_id=actor_id,
        action="merge_source",
        target_type="poster",
        target_id=poster.id,
        summary=f"Merged poster #{source.id} '{source.title}' into poster #{poster.id} '{poster.title}'",
        metadata=metadata,
    )
    db.session.commit()

    return jsonify({
        "item": poster.to_dict(),
        "merged": {"id": source_poster_id, "title": source.title, "urls": merged_urls},
    })


@posters_bp.post("/<int:poster_id>/rebuild-knowledge")
@roles_required("admin")
def rebuild_poster_knowledge_endpoint(poster_id: int):
    poster = Poster.query.get_or_404(poster_id)

    # Clean old knowledge
    PosterNode.query.filter_by(poster_id=poster.id).delete()
    PosterLink.query.filter_by(from_poster_id=poster.id).delete()

    result = rebuild_poster_knowledge(poster)
    db.session.flush()

    actor_id = int(get_jwt_identity())
    create_audit_log(
        actor_id=actor_id,
        action="rebuild_knowledge",
        target_type="poster",
        target_id=poster.id,
        summary=f"Rebuilt knowledge for poster '{poster.title}'",
        metadata={
            "nodes_created": len(result["nodes"]),
            "links_created": len(result["links"]),
        },
    )
    db.session.commit()

    return jsonify({
        "item": poster.to_dict(),
        "nodes_created": len(result["nodes"]),
        "links_created": len(result["links"]),
    })


@posters_bp.route("/<int:poster_id>/ai-enrich", methods=["POST"])
@roles_required("admin")
def ai_enrich(poster_id: int):
    """Trigger AI enrichment (summary, tags, keywords) for a poster."""
    from ..services.ai_service import enrich_poster

    result = enrich_poster(poster_id)
    if not result:
        return jsonify({"error": "Enrichment failed (LLM unavailable or poster not found)"}), 400

    poster = db.session.get(Poster, poster_id)
    if poster:
        poster.content_html = generate_poster_html(
            title=poster.title,
            summary=poster.summary,
            event_time=poster.event_time,
            location=poster.location,
            organizer=poster.organizer,
            activity_type=poster.activity_type,
        )
        db.session.commit()
    return jsonify({"item": poster.to_dict() if poster else None, "ai_result": result})
