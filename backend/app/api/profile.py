from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Notification, Poster


profile_bp = Blueprint("profile", __name__)


def _notification_payload(notification: Notification) -> dict:
    data = notification.to_dict()
    data["read"] = data.pop("is_read", False)
    return data


@profile_bp.get("/me/favorites")
@jwt_required()
def favorite_activities():
    user_id = int(get_jwt_identity())
    redis = getattr(current_app, "redis", None)
    ids = []
    if redis is not None:
        ids = [int(value) for value in redis.smembers(f"user:{user_id}:favorite_activities")]

    posters = Poster.query.filter(Poster.id.in_(ids)).all() if ids else []
    return jsonify({
        "items": [poster.to_dict() for poster in posters],
        "page": 1,
        "per_page": max(len(posters), 1),
        "total": len(posters),
    })


@profile_bp.get("/notifications")
@jwt_required()
def notifications_alias():
    user_id = int(get_jwt_identity())
    notifications = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return jsonify({
        "items": [_notification_payload(item) for item in notifications],
        "total": len(notifications),
    })


@profile_bp.put("/notifications/<int:notification_id>/read")
@jwt_required()
def mark_notification_read_alias(notification_id: int):
    user_id = int(get_jwt_identity())
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user_id:
        return jsonify({"message": "permission denied"}), 403
    notification.is_read = True
    db.session.commit()
    return jsonify({"item": _notification_payload(notification)})


@profile_bp.put("/notifications/read-all")
@jwt_required()
def mark_all_notifications_read():
    user_id = int(get_jwt_identity())
    count = (
        Notification.query
        .filter_by(user_id=user_id, is_read=False)
        .update({"is_read": True})
    )
    db.session.commit()
    return jsonify({"updated": count})
