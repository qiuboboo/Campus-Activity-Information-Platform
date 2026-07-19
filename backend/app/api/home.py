from flask import Blueprint, current_app, jsonify

from ..models import CrawlLog, DataSource, Poster
from ..utils.auth import roles_required

home_bp = Blueprint("home", __name__)


@home_bp.get("/home/featured")
def featured():
    count = 5
    posters = Poster.query.filter_by(status="published").all()

    # Sort by registration count from Redis (if available); fallback to created_at
    redis = getattr(current_app, "redis", None)
    if redis and posters:
        try:
            pipe = redis.pipeline()
            for p in posters:
                pipe.scard(f"activity:{p.id}:registrations")
            reg_counts = dict(zip([p.id for p in posters], pipe.execute()))
            posters.sort(key=lambda p: reg_counts.get(p.id, 0), reverse=True)
        except Exception:
            posters.sort(key=lambda p: p.created_at, reverse=True)
    else:
        posters.sort(key=lambda p: p.created_at, reverse=True)

    posters = posters[:count]

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
                "cover_image_url": p.cover_image_url,
            }
            for p in posters
        ]
    })


@home_bp.get("/demo/summary")
@roles_required("admin")
def admin_summary():
    """Small management-dashboard summary consumed by the frontend."""
    return jsonify({
        "pending": Poster.query.filter(Poster.status.in_(("pending_review", "draft"))).count(),
        "published": Poster.query.filter_by(status="published").count(),
        "sources": DataSource.query.count(),
        "failed_tasks": CrawlLog.query.filter_by(status="failed").count(),
    })
