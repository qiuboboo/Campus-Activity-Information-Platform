from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from ..extensions import db


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    db_ok = True
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = True
    try:
        current_app.redis.ping()
    except Exception:
        redis_ok = False

    status = "ok"
    if not db_ok:
        status = "degraded"

    return jsonify(
        {
            "status": status,
            "database": "ok" if db_ok else "unavailable",
            "redis": "ok" if redis_ok else "unavailable",
            "service": "campus-activity-backend",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
