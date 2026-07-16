"""API blueprint for personal calendar (ICS download + saved events)."""

from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Poster, UserCalendarEvent
from ..services.calendar_service import generate_ics

calendar_bp = Blueprint("calendar", __name__)


def _calendar_event_payload(event: UserCalendarEvent) -> dict:
    poster = event.poster
    event_time = poster.event_time if poster else None
    return {
        "id": event.id,
        "activity_id": event.poster_id,
        "title": poster.title if poster else "",
        "type": poster.activity_type if poster and poster.activity_type else "activity",
        "date": event_time.date().isoformat() if event_time else None,
        "time": event_time.strftime("%H:%M") if event_time else "",
        "event_time": event_time.isoformat() if event_time else None,
    }


# ---------------------------------------------------------------------------
# ICS download (public, no auth required)
# ---------------------------------------------------------------------------


@calendar_bp.get("/posters/<int:poster_id>/ics")
def download_ics(poster_id: int):
    """Download a single poster as an .ics calendar file (public)."""
    poster = Poster.query.get_or_404(poster_id)
    if poster.status != "published":
        return jsonify({"error": "poster not published"}), 404

    ics_content = generate_ics(poster)
    filename = f"activity-{poster_id}.ics"
    response = make_response(ics_content)
    response.headers["Content-Type"] = "text/calendar; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ---------------------------------------------------------------------------
# Personal calendar events (auth required)
# ---------------------------------------------------------------------------


@calendar_bp.post("/calendar/events")
@jwt_required()
def add_calendar_event():
    """Add a poster to 'My Calendar'."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    poster_id = payload.get("poster_id")

    if not poster_id:
        return jsonify({"message": "poster_id is required"}), 400
    poster_id = int(poster_id)

    poster = Poster.query.get(poster_id)
    if not poster or poster.status != "published":
        return jsonify({"error": "poster not found or not published"}), 404

    existing = UserCalendarEvent.query.filter_by(
        user_id=user_id, poster_id=poster_id
    ).first()
    if existing:
        return jsonify({
            "item": existing.to_dict(),
            "event": _calendar_event_payload(existing),
            "already_added": True,
        }), 200

    event = UserCalendarEvent(user_id=user_id, poster_id=poster_id)
    db.session.add(event)
    db.session.commit()
    return jsonify({
        "item": event.to_dict(),
        "event": _calendar_event_payload(event),
        "already_added": False,
    }), 201


@calendar_bp.get("/calendar/events")
@jwt_required()
def list_calendar_events():
    """List 'My Calendar' events, ordered by poster event_time."""
    user_id = int(get_jwt_identity())
    events = (
        UserCalendarEvent.query.filter_by(user_id=user_id)
        .join(Poster, UserCalendarEvent.poster_id == Poster.id)
        .order_by(Poster.event_time.asc().nulls_last())
        .all()
    )
    return jsonify({
        "items": [e.to_dict() for e in events],
        "events": [_calendar_event_payload(e) for e in events],
        "total": len(events),
    })


@calendar_bp.delete("/calendar/events/<int:poster_id>")
@jwt_required()
def remove_calendar_event(poster_id: int):
    """Remove a poster from 'My Calendar'."""
    user_id = int(get_jwt_identity())
    event = UserCalendarEvent.query.filter_by(
        user_id=user_id, poster_id=poster_id
    ).first()
    if not event:
        return jsonify({"error": "event not found in your calendar"}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "event removed from calendar"}), 200


# ---------------------------------------------------------------------------
# (activity-counts endpoint removed — heatmap now uses personal calendar events)
