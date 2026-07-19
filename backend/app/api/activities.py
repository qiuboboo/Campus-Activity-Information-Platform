<<<<<<< Updated upstream
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
=======
"""Compatibility activity API consumed by the Vue frontend.

The original backend calls activities ``Poster`` objects.  This blueprint keeps
that model while exposing the frontend's ``/api/activities`` contract.
"""

import csv
import io
import json
import re

from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, verify_jwt_in_request

from ..extensions import db
from ..models import ActivityAttachment, ActivityFavorite, ActivityRegistration, Notification, Poster, UserCalendarEvent
from ..services.poster_service import build_poster_fields, generate_poster_html
>>>>>>> Stashed changes
from ..utils.auth import roles_required


activities_bp = Blueprint("activities", __name__)

<<<<<<< Updated upstream

def _activity_payload(poster: Poster, *, detail: bool = False) -> dict:
=======
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _tags(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(tag) for tag in parsed if str(tag).strip()]
    except (TypeError, json.JSONDecodeError):
        pass
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _current_user_id() -> int | None:
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()
    return int(identity) if identity else None


def _is_admin() -> bool:
    return bool(get_jwt().get("role") == "admin")


def _can_manage(poster: Poster, user_id: int) -> bool:
    return poster.created_by == user_id or _is_admin()


def _attachment_payloads(poster: Poster) -> list[dict]:
    return [attachment.to_dict() for attachment in poster.attachments]


def _set_attachments(poster: Poster, payload: dict, user_id: int) -> None:
    """Bind only uploaded files owned by the editor; never trust client URLs."""
    if "attachments" not in payload:
        return
    raw = payload.get("attachments") or []
    if not isinstance(raw, list):
        raise ValueError("attachments must be a list")
    ids = [str(item.get("id") or "") for item in raw if isinstance(item, dict)]
    if len(ids) != len(raw) or not all(ids) or len(set(ids)) != len(ids):
        raise ValueError("attachments must reference uploaded file IDs")
    attachments = ActivityAttachment.query.filter(ActivityAttachment.id.in_(ids)).all() if ids else []
    if len(attachments) != len(ids):
        raise ValueError("one or more attachments do not exist")
    if any(attachment.owner_id != user_id and not _is_admin() for attachment in attachments):
        raise ValueError("cannot attach a file owned by another user")
    for attachment in poster.attachments:
        if attachment.id not in ids:
            attachment.poster_id = None
    for attachment in attachments:
        attachment.poster_id = poster.id


def _activity_payload(poster: Poster, user_id: int | None = None, detail: bool = False) -> dict:
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
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
=======
        "created_by": poster.created_by,
        "reject_reason": poster.review_comment,
        "source_url": poster.source_url,
        "content_html": poster.content_html,
    }
    if detail:
        registrations = ActivityRegistration.query.filter_by(poster_id=poster.id)
        payload.update({
            "tags": _tags(poster.tags),
            "attachments": _attachment_payloads(poster),
            "meta": {"views": 0, "registrations": registrations.count()},
            "favorite": bool(user_id and ActivityFavorite.query.filter_by(poster_id=poster.id, user_id=user_id).first()),
            "registered": bool(user_id and registrations.filter_by(user_id=user_id).first()),
            "in_calendar": bool(user_id and UserCalendarEvent.query.filter_by(poster_id=poster.id, user_id=user_id).first()),
>>>>>>> Stashed changes
        })
    return payload


<<<<<<< Updated upstream
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
=======
def _list_response(query, page: int, per_page: int, user_id: int | None = None):
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [_activity_payload(item, user_id) for item in result.items],
        "page": page,
        "per_page": per_page,
        "total": result.total,
    })


def _request_page() -> tuple[int, int]:
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = max(min(request.args.get("per_page", 20, type=int), 100), 1)
    return page, per_page
>>>>>>> Stashed changes


@activities_bp.get("")
def list_activities():
<<<<<<< Updated upstream
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
=======
    user_id = _current_user_id()
    query = Poster.query
    status = (request.args.get("status") or "published").strip()
    if status != "published":
        # A list filter must not disclose drafts or review records publicly.
        # Publishers can inspect only their own activities; admins can inspect
        # the complete review queue.
        if not user_id:
            return jsonify({"message": "permission denied"}), 403
        if not _is_admin():
            query = query.filter_by(created_by=user_id)
    query = query.filter_by(status=status)
    keyword = (request.args.get("q") or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter((Poster.title.like(pattern)) | (Poster.summary.like(pattern)))
    activity_type = (request.args.get("activity_type") or "").strip()
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    # The public activity list is event-centric by default: later event dates
    # appear first unless a caller explicitly asks for latest publication.
    sort = (request.args.get("sort") or "event_time").strip()
    if sort == "event_time":
        # Event-date sorting is newest event first.  Keep undated records at
        # the end so database pagination and the UI have the same order.
        query = query.order_by(Poster.event_time.desc().nulls_last(), Poster.id.desc())
    else:
        query = query.order_by(Poster.created_at.desc())
    page, per_page = _request_page()
    return _list_response(query, page, per_page, user_id)


@activities_bp.get("/mine")
@jwt_required()
def list_my_activities():
    user_id = int(get_jwt_identity())
    page, per_page = _request_page()
    query = Poster.query.filter_by(created_by=user_id).order_by(Poster.created_at.desc())
    status = (request.args.get("status") or "").strip()
    if status:
        query = query.filter_by(status=status)
    return _list_response(query, page, per_page, user_id)


@activities_bp.get("/registered")
@jwt_required()
def list_registered_activities():
    user_id = int(get_jwt_identity())
    page, per_page = _request_page()
    query = (
        Poster.query.join(ActivityRegistration)
        .filter(ActivityRegistration.user_id == user_id)
        .order_by(ActivityRegistration.created_at.desc())
    )
    return _list_response(query, page, per_page, user_id)


@activities_bp.get("/favorites")
@jwt_required()
def list_favorite_activities():
    user_id = int(get_jwt_identity())
    page, per_page = _request_page()
    query = (
        Poster.query.join(ActivityFavorite)
        .filter(ActivityFavorite.user_id == user_id)
        .order_by(ActivityFavorite.created_at.desc())
    )
    return _list_response(query, page, per_page, user_id)


@activities_bp.get("/recommendations")
@jwt_required()
def list_personalized_recommendations():
    from flask import current_app
    if not current_app.config.get("RECOMMENDATION_ENABLED", True):
        return jsonify({"items": []})
    from ..services.knowledge_service import personalized_recommendations

    limit = max(1, min(request.args.get("limit", 6, type=int), 12))
    items = personalized_recommendations(int(get_jwt_identity()), limit)
    return jsonify({
        "items": [
            {**_activity_payload(Poster.query.get(item["activity"]["id"]), int(get_jwt_identity())), "score": item["score"], "reason": item["reason"]}
            for item in items
        ]
    })


@activities_bp.get("/<int:activity_id>")
def get_activity(activity_id: int):
    user_id = _current_user_id()
    poster = Poster.query.get_or_404(activity_id)
    if poster.status != "published" and not (user_id and _can_manage(poster, user_id)):
        return jsonify({"message": "activity not found"}), 404
    return jsonify(_activity_payload(poster, user_id, detail=True))


@activities_bp.get("/<int:activity_id>/related")
def get_related_activities(activity_id: int):
    """Public, explainable recommendations for an activity detail page."""
    user_id = _current_user_id()
    poster = Poster.query.get_or_404(activity_id)
    if poster.status != "published" and not (user_id and _can_manage(poster, user_id)):
        return jsonify({"message": "activity not found"}), 404
    from ..services.knowledge_service import related_payload

    return jsonify(related_payload(poster))
>>>>>>> Stashed changes


@activities_bp.post("")
@roles_required("publisher", "admin")
def create_activity():
    payload = request.get_json(silent=True) or {}
    raw_text = (payload.get("raw_text") or "").strip()
    if not raw_text:
        return jsonify({"message": "raw_text is required"}), 400
<<<<<<< Updated upstream

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
=======
    fields = build_poster_fields(payload)
    fields["tags"] = json.dumps(payload.get("tags") or [], ensure_ascii=False)
    fields["activity_type"] = (payload.get("activity_type") or "").strip() or None
    poster = Poster(created_by=int(get_jwt_identity()), **fields)
    poster.content_html = generate_poster_html(
        poster.title, poster.summary, poster.event_time, poster.location, poster.organizer, poster.activity_type
    )
    db.session.add(poster)
    db.session.flush()
    try:
        _set_attachments(poster, payload, int(get_jwt_identity()))
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"message": str(exc)}), 422
    db.session.commit()
    return jsonify(_activity_payload(poster, int(get_jwt_identity()), detail=True)), 201
>>>>>>> Stashed changes


@activities_bp.put("/<int:activity_id>")
@roles_required("publisher", "admin")
def update_activity(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
<<<<<<< Updated upstream
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
=======
    user_id = int(get_jwt_identity())
    if not _can_manage(poster, user_id):
        return jsonify({"message": "permission denied"}), 403
    payload = request.get_json(silent=True) or {}
    if "raw_text" in payload and not str(payload["raw_text"]).strip():
        return jsonify({"message": "raw_text cannot be empty"}), 400
    fields = build_poster_fields(payload, fallback=poster)
    fields["tags"] = json.dumps(payload.get("tags", _tags(poster.tags)), ensure_ascii=False)
    fields["activity_type"] = (payload.get("activity_type") or poster.activity_type or "").strip() or None
    for key, value in fields.items():
        setattr(poster, key, value)
    poster.content_html = generate_poster_html(
        poster.title, poster.summary, poster.event_time, poster.location, poster.organizer, poster.activity_type
    )
    try:
        _set_attachments(poster, payload, user_id)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 422
    db.session.commit()
    return jsonify(_activity_payload(poster, user_id, detail=True))


@activities_bp.delete("/<int:activity_id>")
@roles_required("publisher", "admin")
def delete_activity(activity_id: int):
    """Delete an activity; admins may delete any activity, publishers only theirs."""
    poster = Poster.query.get_or_404(activity_id)
    user_id = int(get_jwt_identity())
    if not _can_manage(poster, user_id):
        return jsonify({"message": "permission denied"}), 403
    ActivityAttachment.query.filter_by(poster_id=poster.id).update({"poster_id": None})
    UserCalendarEvent.query.filter_by(poster_id=poster.id).delete()
    Notification.query.filter_by(poster_id=poster.id).delete()
    db.session.delete(poster)
    db.session.commit()
    return jsonify({"success": True})
>>>>>>> Stashed changes


@activities_bp.post("/<int:activity_id>/submit-review")
@roles_required("publisher", "admin")
<<<<<<< Updated upstream
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
=======
def submit_activity_for_review(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    user_id = int(get_jwt_identity())
    if not _can_manage(poster, user_id):
        return jsonify({"message": "permission denied"}), 403
    if poster.status != "draft":
        return jsonify({"message": f"cannot submit activity with status '{poster.status}'"}), 400
    poster.status = "pending_review"
    db.session.commit()
    return jsonify(_activity_payload(poster, user_id, detail=True))


@activities_bp.post("/<int:activity_id>/register")
@jwt_required()
def register_for_activity(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    if poster.status != "published":
        return jsonify({"message": "activity is not open for registration"}), 400
    user_id = int(get_jwt_identity())
    existing = ActivityRegistration.query.filter_by(poster_id=poster.id, user_id=user_id).first()
    if existing:
        return jsonify({"success": True, "already_registered": True, "registered": True, "registrations": len(poster.registrations)})
    payload = request.get_json(silent=True) or {}
    form = {key: str(payload.get(key) or "").strip() for key in ("name", "student_id", "college")}
    contact_email = str(payload.get("email") or "").strip()
    if not all(form.values()):
        return jsonify({"message": "name, student_id and college are required"}), 400
    if not contact_email or not _EMAIL_RE.fullmatch(contact_email):
        return jsonify({"message": "a valid contact email is required"}), 400
    if any(len(value) > 100 for value in form.values()):
        return jsonify({"message": "registration field is too long"}), 400
    if len(contact_email) > 120:
        return jsonify({"message": "registration field is too long"}), 400
    registration = ActivityRegistration(poster_id=poster.id, user_id=user_id, contact_email=contact_email, **form)
    db.session.add(registration)
    if UserCalendarEvent.query.filter_by(user_id=user_id, poster_id=poster.id).first() is None:
        db.session.add(UserCalendarEvent(user_id=user_id, poster_id=poster.id))
    db.session.commit()
    return jsonify({"success": True, "already_registered": False, "registered": True, "registrations": len(poster.registrations)})


@activities_bp.delete("/<int:activity_id>/register")
@jwt_required()
def cancel_activity_registration(activity_id: int):
    user_id = int(get_jwt_identity())
    registration = ActivityRegistration.query.filter_by(poster_id=activity_id, user_id=user_id).first()
    if registration is None:
        return jsonify({"message": "registration not found"}), 404
    db.session.delete(registration)
    calendar_event = UserCalendarEvent.query.filter_by(user_id=user_id, poster_id=activity_id).first()
    if calendar_event is not None:
        db.session.delete(calendar_event)
    db.session.commit()
    registrations = ActivityRegistration.query.filter_by(poster_id=activity_id).count()
    return jsonify({"success": True, "registered": False, "registrations": registrations})


@activities_bp.post("/<int:activity_id>/favorite")
@jwt_required()
def favorite_activity(activity_id: int):
    user_id = int(get_jwt_identity())
    poster = Poster.query.get_or_404(activity_id)
    favorite = ActivityFavorite.query.filter_by(poster_id=poster.id, user_id=user_id).first()
    if favorite is None:
        db.session.add(ActivityFavorite(poster_id=poster.id, user_id=user_id))
        db.session.commit()
    return jsonify({"favorite": True})


@activities_bp.delete("/<int:activity_id>/favorite")
@jwt_required()
def remove_activity_favorite(activity_id: int):
    user_id = int(get_jwt_identity())
    favorite = ActivityFavorite.query.filter_by(poster_id=activity_id, user_id=user_id).first()
    if favorite is not None:
        db.session.delete(favorite)
        db.session.commit()
    return jsonify({"favorite": False})


@activities_bp.get("/<int:activity_id>/registrations")
@jwt_required()
def list_activity_registrations(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    user_id = int(get_jwt_identity())
    if not _can_manage(poster, user_id):
        return jsonify({"message": "permission denied"}), 403
    page, per_page = _request_page()
    query = ActivityRegistration.query.filter_by(poster_id=activity_id).order_by(ActivityRegistration.created_at.asc())
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [item.to_dict() for item in result.items], "page": page, "per_page": per_page, "total": result.total})


@activities_bp.get("/<int:activity_id>/registrations.csv")
@jwt_required()
def download_activity_registrations(activity_id: int):
    poster = Poster.query.get_or_404(activity_id)
    user_id = int(get_jwt_identity())
    if not _can_manage(poster, user_id):
        return jsonify({"message": "permission denied"}), 403
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["user_id", "name", "student_id", "college", "email", "registered_at"])
    for item in ActivityRegistration.query.filter_by(poster_id=activity_id).order_by(ActivityRegistration.created_at.asc()):
        writer.writerow([item.user_id, item.name, item.student_id, item.college, item.contact_email or (item.user.email if item.user else ""), item.created_at.isoformat()])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="activity-{activity_id}-registrations.csv"'
    return response
>>>>>>> Stashed changes
