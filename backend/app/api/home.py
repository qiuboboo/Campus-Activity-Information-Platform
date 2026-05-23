from flask import Blueprint, jsonify
from sqlalchemy import desc

from ..models import Poster

home_bp = Blueprint("home", __name__)


@home_bp.get("/home/featured")
def featured():
    posters = (
        Poster.query.filter_by(status="published")
        .order_by(desc(Poster.created_at))
        .limit(3)
        .all()
    )
    return jsonify({
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "summary": p.summary,
                "event_time": p.event_time.isoformat() if p.event_time else None,
                "location": p.location,
                "organizer": p.organizer,
                "activity_type": p.activity_type,
                "created_at": p.created_at.isoformat(),
            }
            for p in posters
        ]
    })
