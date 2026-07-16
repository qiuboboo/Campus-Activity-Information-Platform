from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, verify_jwt_in_request
from sqlalchemy import or_

from ..extensions import db
from ..models import Poster
from ..schemas import paginated
from ..services.audit_service import create_audit_log
from ..services.knowledge_service import rebuild_poster_knowledge
from ..services.notification_service import dispatch_notifications
from ..services.poster_service import build_poster_fields, generate_poster_html
from flask import Response as FlaskResponse
from ..utils.auth import roles_required


activities_bp = Blueprint("activities", __name__)


def _activity_payload(poster: Poster, *, detail: bool = False) -> dict:
    payload = {
        "id": poster.id,
        "title": poster.title,
        "raw_text": poster.raw_text,
        "summary": poster.summary,
        "event_time": poster.event_time.isoformat() if poster.event_time else None,
        "location": poster.location,
        "organizer": poster.organizer,
        "status": poster.status,
        "activity_type": poster.activity_type,
        "created_at": poster.created_at.isoformat(),
        "reject_reason": poster.review_comment,
        "source_url": poster.source_url,
        "cover_image_url": poster.cover_image_url,
    }
    if detail:
        payload.update({
            "tags": [tag.strip() for tag in (poster.tags or "").split(",") if tag.strip()],
            "attachments": [],
            "meta": {"views": 0, "registrations": 0},
            "favorite": False,
            "registered": False,
            "in_calendar": False,
            "content_html": poster.content_html,
        })
    return payload


def _current_user_context() -> tuple[int | None, str | None]:
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        claims = get_jwt()
        return (int(identity), claims.get("role")) if identity else (None, None)
    except Exception:
        return None, None


def _redis_set_key(name: str, activity_id: int) -> str:
    return f"activity:{activity_id}:{name}"


def _user_favorites_key(user_id: int) -> str:
    return f"user:{user_id}:favorite_activities"


def _enrich_user_state(payload: dict, activity_id: int, user_id: int | None) -> dict:
    redis = getattr(current_app, "redis", None)
    registrations = int(redis.scard(_redis_set_key("registrations", activity_id))) if redis else 0
    payload["meta"] = {**payload.get("meta", {}), "registrations": registrations}
    if user_id and redis:
        payload["registered"] = bool(redis.sismember(_redis_set_key("registrations", activity_id), user_id))
        payload["favorite"] = bool(redis.sismember(_user_favorites_key(user_id), activity_id))
    return payload


def _save_activity_payload(poster: Poster, payload: dict) -> None:
    payload = {
        **payload,
        "title": payload.get("title") or getattr(poster, "title", None) or "",
        "summary": payload.get("summary") or getattr(poster, "summary", None) or "",
        "location": payload.get("location") or getattr(poster, "location", None) or "",
        "organizer": payload.get("organizer") or getattr(poster, "organizer", None) or "",
        "source_url": payload.get("source_url") or getattr(poster, "source_url", None) or "",
        "cover_image_url": payload.get("cover_image_url") or getattr(poster, "cover_image_url", None) or "",
        "status": payload.get("status") or getattr(poster, "status", None) or "draft",
        "source_type": payload.get("source_type") or getattr(poster, "source_type", None) or "manual",
    }
    parsed = build_poster_fields(payload, fallback=poster)
    for key, value in parsed.items():
        setattr(poster, key, value)
    poster.activity_type = (payload.get("activity_type") or poster.activity_type or "").strip() or None
    tags = payload.get("tags")
    if isinstance(tags, list):
        poster.tags = ",".join(str(tag).strip() for tag in tags if str(tag).strip()) or None
    poster.content_html = generate_poster_html(
        title=poster.title,
        summary=poster.summary,
        event_time=poster.event_time,
        location=poster.location,
        organizer=poster.organizer,
        activity_type=poster.activity_type,
    )


@activities_bp.get("")
def list_activities():
    keyword = (request.args.get("q") or request.args.get("keyword") or "").strip()
    status = (request.args.get("status") or "published").strip()
    activity_type = (request.args.get("activity_type") or "").strip()
    sort = (request.args.get("sort") or "created_at").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(
        min(int(request.args.get("per_page", current_app.config["POSTERS_PER_PAGE"])), 50),
        1,
    )

    query = Poster.query
    if status:
        query = query.filter_by(status=status)
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    if keyword:
        like_value = f"%{keyword}%"
        query = query.filter(
            or_(
                Poster.title.like(like_value),
                Poster.summary.like(like_value),
                Poster.raw_text.like(like_value),
                Poster.location.like(like_value),
                Poster.organizer.like(like_value),
            )
        )

    if sort == "event_time":
        query = query.order_by(Poster.event_time.asc().nulls_last(), Poster.created_at.desc())
    else:
        query = query.order_by(Poster.created_at.desc())

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated(
        [_activity_payload(poster) for poster in items.items],
        page=page,
        per_page=per_page,
        total=items.total,
    )


@activities_bp.post("")
@roles_required("publisher", "admin")
def create_activity():
    payload = request.get_json(silent=True) or {}
    raw_text = (payload.get("raw_text") or "").strip()
    if not raw_text:
        return jsonify({"message": "raw_text is required"}), 400

    poster = Poster(created_by=int(get_jwt_identity()))
    _save_activity_payload(poster, {**payload, "status": payload.get("status") or "draft"})
    db.session.add(poster)
    db.session.flush()
    db.session.commit()
    return jsonify(_activity_payload(poster, detail=True)), 201


@activities_bp.get("/mine")
@jwt_required()
def list_my_activities():
    user_id = int(get_jwt_identity())
    keyword = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 50), 1)

    query = Poster.query.filter_by(created_by=user_id)
    if status:
        query = query.filter_by(status=status)
    if keyword:
        like_value = f"%{keyword}%"
        query = query.filter(
            or_(
                Poster.title.like(like_value),
                Poster.summary.like(like_value),
                Poster.raw_text.like(like_value),
            )
        )
    query = query.order_by(Poster.created_at.desc())
    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated(
        [_activity_payload(poster) for poster in items.items],
        page=page,
        per_page=per_page,
        total=items.total,
    )


@activities_bp.get("/<int:activity_id>")
def get_activity(activity_id: int):
    user_id, role = _current_user_context()
    poster = Poster.query.get_or_404(activity_id)
    can_view_private = user_id and (role == "admin" or poster.created_by == user_id)
    if poster.status != "published" and not can_view_private:
        return jsonify({"message": "activity not found"}), 404
    payload = _activity_payload(poster, detail=True)
    return jsonify(_enrich_user_state(payload, activity_id, user_id))


@activities_bp.put("/<int:activity_id>")
@roles_required("publisher", "admin")
def update_activity(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    if claims.get("role") != "admin" and poster.created_by != user_id:
        return jsonify({"message": "permission denied"}), 403

    payload = request.get_json(silent=True) or {}
    if payload.get("raw_text") is not None and not str(payload.get("raw_text")).strip():
        return jsonify({"message": "raw_text cannot be empty"}), 400
    _save_activity_payload(poster, payload)
    db.session.commit()
    return jsonify(_activity_payload(poster, detail=True))


@activities_bp.post("/<int:activity_id>/submit-review")
@roles_required("publisher", "admin")
def submit_activity(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    if claims.get("role") != "admin" and poster.created_by != user_id:
        return jsonify({"message": "permission denied"}), 403
    if poster.status not in {"draft", "rejected"}:
        return jsonify({"message": f"cannot submit activity with status '{poster.status}'"}), 400

    poster.status = "pending_review"
    create_audit_log(
        actor_id=user_id,
        action="submit",
        target_type="poster",
        target_id=poster.id,
        summary=f"Submitted activity '{poster.title}' for review",
    )
    db.session.commit()
    return jsonify(_activity_payload(poster, detail=True))


@activities_bp.route("/<int:activity_id>/register", methods=["POST", "DELETE"])
@jwt_required()
def register_activity(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    if poster.status != "published":
        return jsonify({"message": "activity not found"}), 404
    redis = getattr(current_app, "redis", None)
    if redis is None:
        return jsonify({"message": "registration service unavailable"}), 503

    user_id = int(get_jwt_identity())
    key = _redis_set_key("registrations", activity_id)

    if request.method == "DELETE":
        redis.srem(key, user_id)
        return jsonify({
            "success": True,
            "registrations": int(redis.scard(key)),
            "registered": False,
        })

    already_registered = bool(redis.sismember(key, user_id))
    if not already_registered:
        redis.sadd(key, user_id)
    return jsonify({
        "success": True,
        "registrations": int(redis.scard(key)),
        "already_registered": already_registered,
    })


@activities_bp.route("/<int:activity_id>/favorite", methods=["POST", "DELETE"])
@jwt_required()
def favorite_activity(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    if poster.status != "published":
        return jsonify({"message": "activity not found"}), 404
    redis = getattr(current_app, "redis", None)
    if redis is None:
        return jsonify({"message": "favorite service unavailable"}), 503

    user_id = int(get_jwt_identity())
    key = _user_favorites_key(user_id)
    if request.method == "POST":
        redis.sadd(key, activity_id)
        favorite = True
    else:
        redis.srem(key, activity_id)
        favorite = False
    return jsonify({"favorite": favorite})


@activities_bp.get("/<int:activity_id>/poster-html")
def poster_html(activity_id: int):
    """Return a standalone HTML poster page for this activity (public)."""
    poster = Poster.query.get_or_404(activity_id)
    html = generate_poster_html(
        title=poster.title,
        summary=poster.summary,
        event_time=poster.event_time,
        location=poster.location,
        organizer=poster.organizer,
        activity_type=poster.activity_type,
    )
    return FlaskResponse(html, mimetype="text/html")
