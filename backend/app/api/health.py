from datetime import datetime, timezone

from flask import Blueprint, jsonify
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

    return jsonify(
        {
            "status": "ok" if db_ok else "degraded",
            "database": "ok" if db_ok else "unavailable",
            "service": "campus-activity-backend",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
