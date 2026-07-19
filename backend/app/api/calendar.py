"""API blueprint for personal calendar (ICS download + saved events)."""

from flask import Blueprint, jsonify, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required

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
    calendar_events = []
    for event in events:
        poster = event.poster
        if poster is None:
            continue
        event_time = poster.event_time.isoformat() if poster.event_time else None
        calendar_events.append({
            "id": event.id,
            "title": poster.title,
            "time": poster.event_time.strftime("%H:%M") if poster.event_time else "全天",
            "type": "activity",
            "date": poster.event_time.date().isoformat() if poster.event_time else None,
            "event_time": event_time,
            "activity_id": poster.id,
        })
    return jsonify({
        "items": [e.to_dict() for e in events],
        "events": calendar_events,
        "total": len(events),
    })
